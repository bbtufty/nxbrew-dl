import copy
import os
import shutil
import time
from urllib.parse import urlparse

import myjdapi
import numpy as np
from pathvalidate import sanitize_filename

import nxbrew_dl
from ..util import (
    NXBrewLogger,
    discord_push,
    load_yml,
    load_json,
    save_json,
    get_html_page,
    get_languages,
    get_thumb_url,
    get_dl_dict,
    bypass_ouo,
    bypass_1link,
)


def add_ordered_score(
    releases,
    dl_dict,
    priorities,
    score_key,
):
    """Add an ordered score, include the priority of the order

    Args:
        releases (list): List of releases to score
        dl_dict (dict): Dictionary of potential downloads
        priorities (list): List of values in priority order
        score_key (str): Corresponding score key for the priorities in the rom_dict
    """

    score_dict = {}

    # Go backwards so the first entry is the highest priority
    for i, prio in enumerate(priorities[::-1]):
        score_dict[prio] = i + 1

    scores = np.zeros_like(releases, dtype=int)
    for i, r in enumerate(releases):
        for key in dl_dict[r][score_key]:
            if key in score_dict:
                scores[i] += score_dict[key]

    return scores


class NXBrew:

    def __init__(
        self,
        to_download,
        progress_bar=None,
        progress_bar_label=None,
        update_progressBar=None,
        general_config=None,
        regex_config=None,
        user_config=None,
        user_cache=None,
        logger=None,
    ):
        """Handles downloading files

        Will search through download sites in priority, pulling out links and sending them
        to JDownloader. If they're all online, will bulk download/extract, and then
        remove the links

        Args:
            to_download (dict): Dictionary of files to download
            progress_bar (QProgressBar, optional): Progress bar widget.
                Defaults to None, which will do nothing fancy with the
                progress bar
            progress_bar_label (QLabel, optional): If set, will put
                the game title in a progress bar label. Defaults to
                None
            general_config (dict): Dictionary for default configuration
            regex_config (dict): Dictionary for regex configuration
            user_config (dict): Dictionary for user configuration
            user_cache (dict): Cache dictionary
            logger (logging.logger): Logger instance. If None, will set up a new one
        """

        # Load in various config files, if they're not already loaded
        self.mod_dir = os.path.dirname(nxbrew_dl.__file__)

        general_config_filename = os.path.join(self.mod_dir, "configs", "general.yml")
        if general_config is None:
            general_config = load_yml(general_config_filename)
        self.general_config = general_config
        self.dl_mappings = self.general_config["dl_mappings"]

        regex_config_filename = os.path.join(self.mod_dir, "configs", "regex.yml")
        if regex_config is None:
            regex_config = load_yml(regex_config_filename)
        self.regex_config = regex_config

        # Read in the user config
        user_config_file = os.path.join(os.getcwd(), "config.yml")
        if user_config is None:
            if os.path.exists(user_config_file):
                user_config = load_yml(user_config_file)
            else:
                user_config = {}
        self.user_config = user_config

        self.region_prefs = self.user_config["regions"]
        self.language_prefs = self.user_config["languages"]

        # Add an "All" at the start of prefs as a catch-all
        self.region_prefs.insert(0, "All")
        self.language_prefs.insert(0, "All")

        # Read in user cache, keeping the filename around so we can save it out later
        user_cache_file = os.path.join(os.getcwd(), "cache.json")
        if user_cache is None:
            if os.path.exists(user_cache_file):
                user_cache = load_json(user_cache_file)
            else:
                user_cache = {}
        self.user_cache = user_cache
        self.user_cache_file = user_cache_file

        if logger is None:
            logger = NXBrewLogger(log_level="INFO")
        self.logger = logger

        # Set up JDownloader
        self.logger.info("Connecting to JDownloader")
        jd = myjdapi.Myjdapi()
        jd.set_app_key("nxbrewdl")

        jd.connect(self.user_config["jd_user"], self.user_config["jd_pass"])

        jd_device_name = self.user_config["jd_device"]

        # Redact the device name
        self.logger.update_redact_filter(jd_device_name)

        self.logger.info(f"Connecting to device {jd_device_name}")
        self.jd_device = jd.get_device(jd_device_name)

        # Discord stuff
        discord_url = self.user_config.get("discord_url", "")
        if discord_url == "":
            discord_url = None
        self.discord_url = discord_url

        self.to_download = to_download
        self.progress_bar = progress_bar
        self.progress_bar_label = progress_bar_label
        self.update_progressBar = update_progressBar

        self.dry_run = self.user_config.get("dry_run", False)

    def run(self):
        """Run NXBrew-dl"""

        n_downloads = len(self.to_download)

        if self.progress_bar is not None:
            # Reset progress bar to 0
            self.update_progressBar.emit(0)

        self.logger.info("")
        self.logger.info(f"=" * 80)
        self.logger.info(f"{' ' * 30}STARTING NXBREW-DL{' ' * 30}")
        self.logger.info(f"=" * 80)

        for i_name, name in enumerate(self.to_download):

            progress_val = 100 * (i_name + 1) / n_downloads

            url = self.to_download[name]

            if self.progress_bar is not None:
                self.progress_bar_label.setText(f"{i_name + 1}/{n_downloads}: {name}")

            self.logger.info("")
            self.logger.info(f"=" * 80)
            self.logger.info(f"Starting download for: {name}")
            self.logger.info("")
            self.download_game(
                name=name,
                url=url,
            )
            self.logger.info(f"=" * 80)
            self.logger.info("")

            if self.progress_bar is not None:
                # Reset progress bar to 0
                self.update_progressBar.emit(progress_val)

        # Clean up
        self.logger.info("Performing final cache/disk clean up")
        self.logger.info("")

        self.clean_up_cache()

        self.logger.info("All done!")
        self.logger.info("")

        return True

    def download_game(
        self,
        name,
        url,
    ):
        """Download game given URL

        Will grab the HTML page, parse out files, then remove
        based on region/language preferences. If we don't
        want DLC/Updates it'll also remove them before sending
        off to JDownloader

        Args:
            name (str): Name of game to download
            url (str): URL to download
        """

        # Get the soup
        soup = get_html_page(
            url,
            cache_filename="game.html",
        )

        # Get thumbnail URL
        thumb_url = get_thumb_url(
            soup,
        )

        # Get languages
        langs = get_languages(
            soup,
            lang_dict=self.general_config["languages"],
        )
        langs.sort()

        self.logger.info(f"Found languages across all releases:")
        for l in langs:
            self.logger.info(f"\t{l}")
        self.logger.info("")

        # If the language we want isn't in here, then skip
        found_language = False
        for lang in langs:
            for lang_pref in self.language_prefs:
                if lang == lang_pref:
                    found_language = True
                    break
            if found_language:
                break

        if not found_language:
            self.logger.warning(f"Did not find any requested language:")
            for l in self.language_prefs:
                self.logger.warning(f"\t{l}")
            self.logger.warning("")
            return False

        # Pull out useful things from the config
        regions = list(self.general_config["regions"].keys())
        regionless_titles = self.general_config["regionless_titles"]
        languages = self.general_config["languages"]
        implied_languages = self.general_config["implied_languages"]
        dl_sites = self.general_config["dl_sites"]

        dl_dict = get_dl_dict(
            soup,
            regions=regions,
            regionless_titles=regionless_titles,
            languages=languages,
            implied_languages=implied_languages,
            dl_sites=dl_sites,
            dl_mappings=self.dl_mappings,
        )
        n_releases = len(dl_dict)

        if n_releases == 0:
            raise ValueError("No releases found")

        self.logger.info(f"Found {n_releases} release(s):")

        for release in dl_dict:
            self.logger.info(f"\tRegion(s):")
            for r in dl_dict[release]["regions"]:
                self.logger.info(f"\t\t{r}")

            self.logger.info(f"\tLanguages(s):")
            for l in dl_dict[release]["languages"]:
                self.logger.info(f"\t\t{l}")

            # Loop over the various file types, and print out the links and associated
            # sites
            for dl_mapping in self.dl_mappings:

                for dl_tag in self.dl_mappings[dl_mapping]["dl_tags"]:

                    clean_dl_name = self.dl_mappings[dl_mapping]["dl_tags"][dl_tag][
                        "dl_name_mapping"
                    ]

                    if any([key == dl_tag for key in dl_dict[release]]):
                        self.logger.info(f"\t{clean_dl_name}:")
                        for release_dl in dl_dict[release][dl_tag]:
                            self.logger.info(f"\t\t{release_dl['full_name']}:")

                            for dl_site in dl_sites:
                                if dl_site in release_dl:
                                    self.logger.info(f"\t\t\t{dl_site}:")
                                    for dl_link in release_dl[dl_site]:
                                        # Redact the DL link
                                        self.logger.update_redact_filter(dl_link)

                                        self.logger.info(f"\t\t\t- {dl_link}")

            self.logger.info("")

        # Remove if it's not a region or language we want

        pref_mapping = {
            "regions": self.region_prefs,
            "languages": self.language_prefs,
        }

        for key in ["regions", "languages"]:

            prefs = pref_mapping[key]

            releases_to_remove = []
            for release in dl_dict:

                found = False

                release_vals = dl_dict[release][key]
                for val in release_vals:
                    for pref in prefs:
                        if val == pref:
                            found = True
                            break
                    if found:
                        break

                if not found:
                    releases_to_remove.append(release)

            if len(releases_to_remove) > 0:
                self.logger.info(f"Removing unwanted release(s) based on {key}:")
                for release in releases_to_remove:
                    self.logger.info(f"\t{'/'.join(dl_dict[release]['regions'])}")
                    dl_dict.pop(release)
                self.logger.info("")

        if len(dl_dict) > 1:
            self.logger.info(
                "Multiple suitable releases found. Will score to find most suitable"
            )
            best_release = self.get_dl_dict_score(dl_dict=dl_dict)

            # Now remove anything that's not the best release
            releases_to_remove = []
            for r in dl_dict:
                if r not in best_release:
                    releases_to_remove.append(r)

            if len(releases_to_remove) > 0:
                self.logger.info("Removing lower scored release(s):")
                for release in releases_to_remove:
                    self.logger.info(f"\t{'/'.join(dl_dict[release]['regions'])}")
                    dl_dict.pop(release)
                self.logger.info("")

            # If we're still too long, then bug out
            if len(dl_dict) > 1:
                raise NotImplementedError(
                    "Multiple suitable releases found. Unsure how to deal with this right now"
                )

        if len(dl_dict) == 0:
            self.logger.warning(
                "No suitable releases found (consider changing language/region preferences). "
                "Will skip"
            )
            return False

        # Trim down to just one ROM
        release = list(dl_dict.keys())[0]
        dl_dict = dl_dict[release]

        if "base_game_nsp" in dl_dict and "base_game_xci" in dl_dict:
            self.logger.info("Found both NSP and XCI:")

            if self.user_config["prefer_filetype"] == "NSP":
                self.logger.info(f"\tRemoving XCI")
                dl_dict.pop("base_game_xci")
            elif self.user_config["prefer_filetype"] == "XCI":
                self.logger.info(f"\tRemoving NSP")
                dl_dict.pop("base_game_nsp")
            else:
                raise ValueError("Expecting preferred filetype to be one of NSP, XCI")
            self.logger.info("")

        if not self.user_config["download_dlc"]:
            self.logger.info("Removing DLC")
            removed_dict = dl_dict.pop("dlc", [])

            # If we've removed anything, say so here
            if len(removed_dict) > 0:
                for r in removed_dict:
                    self.logger.info(f"\t- {r['full_name']}")

            self.logger.info("")

        if not self.user_config["download_update"]:
            self.logger.info("Removing updates")
            removed_dict = dl_dict.pop("update", [])

            # If we've removed anything, say so here
            if len(removed_dict) > 0:
                for r in removed_dict:
                    self.logger.info(f"\t- {r['full_name']}")

            self.logger.info("")

        if self.dry_run:
            self.logger.info("Dry run, will not download anything")
            return True

        # If we've updated URLs, check for that here and update as appropriate
        if url not in self.user_cache:
            url_path = urlparse(url).path
            for cache_url in self.user_cache:
                cache_url_path = urlparse(cache_url).path

                # If we match, rename and delete
                if url_path == cache_url_path:
                    self.user_cache[url] = self.user_cache[cache_url]
                    del self.user_cache[cache_url]
                    break

        # Add unique URL to cache if it's not already there
        if url not in self.user_cache:
            self.logger.debug(f"Adding {name} to cache")
            self.user_cache[url] = {}
            self.user_cache[url]["name"] = name

        # Add thumbnail URL to cache if it's not already there, or potentially update
        if "thumb_url" not in self.user_cache[url]:
            self.logger.debug("Adding thumbnail URL to cache")
            self.user_cache[url]["thumb_url"] = thumb_url
        if self.user_cache[url]["thumb_url"] != thumb_url:
            self.logger.debug("Updating thumbnail URL")
            self.user_cache[url]["thumb_url"] = thumb_url

        # Hooray! We're finally ready to start downloading. Map things to folder and let's get going
        self.logger.info("Beginning download process:")

        for dl_mapping in self.dl_mappings:
            dl_dir = self.dl_mappings[dl_mapping]["directory_name"]

            for dl_key in self.dl_mappings[dl_mapping]["dl_tags"]:

                # If we don't have anything to download, skip
                if dl_key not in dl_dict:
                    continue

                dl_key_clean = self.dl_mappings[dl_mapping]["dl_tags"][dl_key][
                    "dl_name_mapping"
                ]

                if dl_key not in self.user_cache[url]:
                    self.user_cache[url][dl_key] = []

                # Loop over items in the list
                for dl_info in dl_dict[dl_key]:

                    if dl_info["full_name"] in self.user_cache[url][dl_key]:
                        self.logger.info(
                            f"\t{dl_key_clean}: {dl_info['full_name']} already downloaded. Will skip"
                        )
                    else:
                        self.logger.info(
                            f"\tDownloading {dl_key_clean}: {dl_info['full_name']}"
                        )
                        out_dir = os.path.join(self.user_config["download_dir"], dl_dir)

                        # Sanitize the package name so we're safe here
                        package_name = sanitize_filename(name)

                        self.run_jdownloader(
                            dl_dict=dl_info,
                            out_dir=out_dir,
                            package_name=package_name,
                        )
                        self.logger.info("")

                        # Update and save out cache
                        self.user_cache[url][dl_key].append(dl_info["full_name"])
                        save_json(
                            self.user_cache,
                            self.user_cache_file,
                            sort_key="name",
                        )

                        # Post to discord
                        if self.discord_url is not None:
                            self.post_to_discord(
                                name=name,
                                url=url,
                                added_type=dl_key_clean,
                                description=dl_info["full_name"],
                                thumb_url=thumb_url,
                            )

        self.logger.info("")
        self.logger.info("All downloads complete")

        return True

    def get_dl_dict_score(
        self,
        dl_dict,
    ):
        """Get the best ROM(s) from a list, using a scoring system

        We only score by language and region, preferring a particular
        region over a particular language

        Args:
            dl_dict: Dictionary of potential downloads
        """

        language_score = 1e2
        region_score = 1e4

        releases = list(dl_dict.keys())
        release_scores = np.zeros(len(releases))

        # Language priorities
        language_score_to_add = add_ordered_score(
            releases=releases,
            dl_dict=dl_dict,
            priorities=self.language_prefs,
            score_key="languages",
        )
        release_scores += language_score * (1 + (language_score_to_add - 1) / 100)

        # Regions priorities
        region_score_to_add = add_ordered_score(
            releases=releases,
            dl_dict=dl_dict,
            priorities=self.region_prefs,
            score_key="regions",
        )
        release_scores += region_score * (1 + (region_score_to_add - 1) / 100)

        best_release_idx = np.where(release_scores == np.nanmax(release_scores))[0]
        releases = np.asarray(releases)[best_release_idx]

        return releases

    def run_jdownloader(
        self,
        dl_dict,
        out_dir,
        package_name,
    ):
        """Grab links and download through JDownloader

        Will look through download sites in priority order,
        bypassing shortened links if required and checking
        everything's online. Then, will download, extract,
        and clean up at the end

        Args:
            dl_dict (dict): Dictionary of download files
            out_dir: Directory to save downloaded files
            package_name (str): Name of package to define subdirectories
                and keep track of links
        """

        package_id = None
        dl_site = None

        # Loop over download sites, hit the first one we find
        for dl_site in self.general_config["dl_sites"]:

            if dl_site in self.general_config["dl_sites_no_jdownload"]:
                self.logger.info(f"JDownloader does not support {dl_site}, skipping")
                continue

            if dl_site in dl_dict:
                dl_links = dl_dict[dl_site]
                self.logger.info(f"\t\tTrying {dl_site}:")

                for d in dl_links:

                    # Redact the link
                    self.logger.update_redact_filter(d)

                    self.logger.info(f"\t\t\tLink: {d}")
                    if "ouo" in d:
                        self.logger.info(
                            f"\t\t\t\t{d} detected as OUO shortened link. Will bypass"
                        )
                        d_final = bypass_ouo(d, logger=self.logger)
                    elif "1link" in d:
                        self.logger.info(
                            f"\t\t\t\t{d} detected as 1link shortened link. Will bypass"
                        )
                        d_final = bypass_1link(d, logger=self.logger)
                    else:
                        d_final = copy.deepcopy(d)

                    # Redact the link
                    self.logger.update_redact_filter(d_final)

                    self.logger.info(f"\t\t\t\tAdding {d_final} to JDownloader")
                    self.jd_device.linkgrabber.add_links(
                        [
                            {
                                "autostart": False,
                                "links": d_final,
                                "destinationFolder": out_dir,
                                "packageName": package_name,
                            }
                        ]
                    )

                # Check that the package has been added
                package_added = False
                while not package_added:
                    time.sleep(1)

                    package_list = self.jd_device.linkgrabber.query_packages()

                    for p in package_list:

                        if package_added:
                            continue

                        if p["name"] == package_name:
                            package_added = True

                # Check that all links have been added
                all_added = False
                while not all_added:
                    time.sleep(1)
                    package_list = self.jd_device.linkgrabber.query_packages()

                    found_package = False
                    child_count = None

                    for p in package_list:

                        if found_package:
                            continue

                        if p["name"] == package_name:
                            child_count = p["childCount"]
                            found_package = True

                    if child_count == len(dl_links):
                        all_added = True

                # Next up, we want to do a check that all the files are online and happy
                package_list = self.jd_device.linkgrabber.query_packages()
                for p in package_list:
                    if p["name"] == package_name:
                        package_id = p["uuid"]
                        break

                if package_id is None:
                    raise ValueError(
                        f"Did not find associated package with name {package_name}"
                    )

                file_list = self.jd_device.linkgrabber.query_links()
                any_offline = False
                for f in file_list:
                    if f["packageUUID"] == package_id:
                        if not f["availability"] == "ONLINE":
                            self.logger.warning(
                                "\t\t\tLink(s) offline, will remove and try with another download client"
                            )
                            any_offline = True
                            break

                if any_offline:
                    self.jd_device.linkgrabber.remove_links(package_ids=[package_id])
                    continue

                break

        if dl_site is None:
            raise ValueError("Expecting dl_site to be defined")

        if package_id is None:
            raise ValueError("Expecting the package_id to be defined")

        # Finally, we need to pull the links out as well to move them
        # to the download list
        link_list = self.jd_device.linkgrabber.query_links()
        link_ids = []
        for l in link_list:
            if l["packageUUID"] == package_id:
                link_ids.append(l["uuid"])

        # Hooray! We've got stuff online. Start downloading
        self.logger.info(f"\t\t\tSuccess! Will download from {dl_site}")
        self.logger.info(f"\t\tStarting download")
        self.jd_device.linkgrabber.move_to_downloadlist(
            link_ids=link_ids, package_ids=[package_id]
        )

        # The package ID changes when it moves to downloads so find it again
        package_id = None

        package_list = self.jd_device.downloads.query_packages()
        for p in package_list:
            if p["name"] == package_name:
                package_id = p["uuid"]
                break

        # If everything's offline, then we'll fail here, so warn and return
        if package_id is None:
            self.logger.warning(
                f"Did not find associated package with name {package_name}"
            )
            return True

        # Query status occasionally, to make sure the download is complete and
        # extraction is done
        finished = False
        while not finished:
            time.sleep(1)
            dl_status = self.jd_device.downloads.query_packages(
                [
                    {
                        "packageUUIDs": [package_id],
                        "status": True,
                        "finished": True,
                    }
                ]
            )
            if "finished" not in dl_status[0]:
                finished = False
            else:
                finished = dl_status[0]["finished"]

            # Hunt through to make sure extraction is also complete,
            # only once everything is downloaded
            if finished:
                dl_status = self.jd_device.downloads.query_links(
                    [
                        {
                            "packageUUIDs": [package_id],
                            "status": True,
                            "extractionStatus": True,
                            "finished": True,
                        }
                    ]
                )
                for status in dl_status:
                    if "extractionStatus" in status:
                        if status["extractionStatus"] != "SUCCESSFUL":
                            finished = False
                            break

        # Wait for a bit, just to ensure everything is good
        time.sleep(5)

        self.logger.info("\t\tFiles successfully downloaded")

        # And finally, cleanup
        self.jd_device.downloads.cleanup(
            action="DELETE_FINISHED",
            mode="REMOVE_LINKS_ONLY",
            selection_type="SELECTED",
            package_ids=[package_id],
        )

        self.logger.info("\t\tLinks removed from JDownloader")

        return True

    def post_to_discord(
        self, name, url, added_type="Base Game", description=None, thumb_url=None
    ):
        """Post summary as a discord message

        Args:
            name (str): Game name
            url (str): URL for the ROM
            added_type (str): Type of added link. Defaults to "Base Game"
            description (str): Description of the link. Defaults to None
            thumb_url (str): Thumbnail URL. Defaults to None
        """

        embeds = [
            {
                "author": {
                    "name": name,
                    "url": url,
                },
                "title": added_type,
                "description": description,
                "thumbnail": {"url": thumb_url},
            }
        ]

        discord_push(
            url=self.discord_url,
            embeds=embeds,
        )

        return True

    def clean_up_cache(self):
        """Remove items from the cache and on disk, if needed, and do a final save"""

        # First, scan through for any games that are no longer check
        games = [g for g in self.to_download]
        games_to_delete = []
        keys_to_delete = []

        for d in self.user_cache:
            cache_game = self.user_cache[d]["name"]
            if cache_game not in games:
                games_to_delete.append(cache_game)
                keys_to_delete.append(d)

        if len(games_to_delete) > 0:

            self.logger.info(f"\tRemoving games:")

            for i, g in enumerate(games_to_delete):

                g_sanitized = sanitize_filename(g)

                for dl_mapping in self.dl_mappings:
                    dl_dir = self.dl_mappings[dl_mapping]["directory_name"]
                    g_dir = os.path.join(
                        self.user_config["download_dir"],
                        dl_dir,
                        g_sanitized,
                    )
                    if os.path.exists(g_dir):
                        self.logger.info(f"\t\tRemoving {g}: {dl_mapping}")
                        shutil.rmtree(g_dir)

                # And remove from the cache
                self.user_cache.pop(keys_to_delete[i])

            self.logger.info("")

        # Now, do a pass where we'll get rid of DLC/updates if they're no longer requested
        for key in ["dlc", "update"]:
            if not self.user_config[f"download_{key}"]:

                dl_mapping = {
                    "dlc": "DLC",
                    "update": "Update",
                }[key]

                dl_key_clean = self.dl_mappings[dl_mapping]["dl_tags"][key][
                    "dl_name_mapping"
                ]
                dl_dir = self.dl_mappings[dl_mapping]["directory_name"]

                self.logger.info(f"\tRemoving {dl_key_clean} from cache and disk")
                out_dir = os.path.join(
                    self.user_config["download_dir"],
                    dl_dir,
                )
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)

                for d in self.user_cache:
                    self.user_cache[d].pop(key, [])

        # Save out the cache
        save_json(
            self.user_cache,
            self.user_cache_file,
            sort_key="name",
        )

        return True
