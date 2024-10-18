import copy
import os
import time
import shutil

import myjdapi

import nxbrew_dl
from ..gui.gui_utils import get_gui_logger
from ..util import (
    load_yml,
    load_json,
    save_json,
    get_html_page,
    get_languages,
    get_dl_dict,
    bypass_ouo,
)

DL_MAPPING = {
    "base_game_nsp": "Games",
    "base_game_xci": "Games",
    "dlc": "DLC",
    "update": "Updates",
}

class NXBrew:

    def __init__(
        self,
        to_download,
        logger=None,
    ):
        """Handles downloading files

        Will search through download sites in priority, pulling out links and sending them
        to JDownloader. If they're all online, will bulk download/extract, and then
        remove the links

        Args:
            to_download (dict): Dictionary of files to download
            logger (logging.logger): Logger instance. If None, will set up a new one
        """

        # Load in various config files
        self.mod_dir = os.path.dirname(nxbrew_dl.__file__)
        self.general_config = load_yml(
            os.path.join(self.mod_dir, "configs", "general.yml")
        )
        self.regex_config = load_yml(os.path.join(self.mod_dir, "configs", "regex.yml"))

        # Read in the user config, keeping the filename around so we can save it out later
        self.user_config_file = os.path.join(os.getcwd(), "config.yml")
        if os.path.exists(self.user_config_file):
            self.user_config = load_yml(self.user_config_file)
        else:
            self.user_config = {}

        # Read in user cache, keeping the filename around so we can save it out later
        self.user_cache_file = os.path.join(os.getcwd(), "cache.json")
        if os.path.exists(self.user_cache_file):
            self.user_cache = load_json(self.user_cache_file)
        else:
            self.user_cache = {}

        if logger is None:
            logger = get_gui_logger(log_level="INFO")
        self.logger = logger

        # Set up JDownloader
        self.logger.info("Connecting to JDownloader")
        jd = myjdapi.Myjdapi()
        jd.set_app_key("nxbrewdl")

        jd.connect(self.user_config["jd_user"], self.user_config["jd_pass"])

        jd_device_name = self.user_config["jd_device"]
        self.logger.info(f"Connecting to device {jd_device_name}")
        self.jd_device = jd.get_device(jd_device_name)

        self.to_download = to_download

    def run(self):
        """Run NXBrew-dl"""

        for name in self.to_download:

            url = self.to_download[name]

            self.logger.info(f"=" * 80)
            self.logger.info(f"Starting download for: {name}")
            self.download_game(
                name=name,
                url=url,
            )
            self.logger.info(f"=" * 80)

        self.logger.info("All downloads completed")

        self.logger.info("Cleaning up")

        self.clean_downloads()

        self.logger.info("All done!")

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

        if url not in self.user_cache:
            self.user_cache[url] = {}
            self.user_cache[url]["name"] = name

        # TODO: For now, we only allow English releases. Make this configurable later
        allowed_regions = ["All", "USA"]
        allowed_languages = ["English"]

        # Get the soup
        soup = get_html_page(
            url,
            cache_filename="game.html",
        )

        langs = get_languages(
            soup,
            lang_dict=self.general_config["languages"],
        )

        self.logger.info(f"Found languages: {', '.join(langs)}")

        # If the language we want isn't in here, then skip
        found_language = False
        for lang in langs:
            for allowed_lang in allowed_languages:
                if lang == allowed_lang:
                    found_language = True

        if not found_language:
            self.logger.warning(
                f"Did not find any requested language: {allowed_languages}"
            )
            return False

        # Pull out useful things from the config
        regions = list(self.general_config["regions"].keys())
        dl_sites = self.general_config["dl_sites"]
        dl_names = self.general_config["dl_names"]

        dl_dict = get_dl_dict(
            soup,
            regions=regions,
            dl_sites=dl_sites,
            dl_names=dl_names,
        )
        n_releases = len(dl_dict)

        self.logger.info(f"Found {n_releases} releases:")

        for release in dl_dict:
            self.logger.info(f"Region(s): {'/'.join(dl_dict[release]['regions'])}")

            if any([key == "base_game_nsp" for key in dl_dict[release]]):
                self.logger.info("\tHas NSP")
            if any([key == "base_game_xci" for key in dl_dict[release]]):
                self.logger.info("\tHas XCI")
            if any([key == "dlc" for key in dl_dict[release]]):
                self.logger.info("\tHas DLC")
            if any([key == "update" for key in dl_dict[release]]):
                self.logger.info("\tHas Update")
            self.logger.info("")

        releases_to_remove = []
        for release in dl_dict:

            found_region = False

            release_regions = dl_dict[release]["regions"]
            for release_region in release_regions:
                for allowed_region in allowed_regions:
                    if release_region == allowed_region:
                        found_region = True

            if not found_region:
                releases_to_remove.append(release)

        if len(releases_to_remove) > 0:
            self.logger.info("Removing unwanted regions:")
            for release in releases_to_remove:
                self.logger.info(f"\t{'/'.join(dl_dict[release]['regions'])}")
                dl_dict.pop(release)

        if len(dl_dict) > 1:
            raise NotImplementedError(
                "Multiple suitable releases found. Unsure how to deal with this right now"
            )

        # Trim down to just our one ROM
        release = list(dl_dict.keys())[0]
        dl_dict = dl_dict[release]

        if "base_game_nsp" in dl_dict and "base_game_xci" in dl_dict:
            self.logger.info("Found both NSP and XCI")

            if self.user_config["prefer_filetype"] == "NSP":
                dl_dict.pop("base_game_xci")
            elif self.user_config["prefer_filetype"] == "XCI":
                dl_dict.pop("base_game_nsp")
            else:
                raise ValueError("Expecting preferred filetype to be one of NSP, XCI")

        if not self.user_config["download_dlc"]:
            self.logger.info("Removing any DLC")
            dl_dict.pop("dlc", [])

        if not self.user_config["download_update"]:
            self.logger.info("Removing any updates")
            dl_dict.pop("update", [])

        # Hooray! We're finally ready to start downloading. Map things to folder and let's get going

        for dl_key in DL_MAPPING:

            dl_dir = DL_MAPPING[dl_key]

            # If we don't have anything to download, skip
            if dl_key not in dl_dict:
                continue

            if dl_key not in self.user_cache[url]:
                self.user_cache[url][dl_key] = []

            # Loop over items in the list
            for dl_info in dl_dict[dl_key]:

                if dl_info["full_name"] in self.user_cache[url][dl_key]:
                    self.logger.info(
                        f"{dl_info['full_name']} already downloaded. Will skip"
                    )
                else:
                    self.logger.info(f"Downloading {dl_key}: {dl_info['full_name']}")
                    out_dir = os.path.join(self.user_config["download_dir"], dl_dir)

                    self.run_jdownloader(
                        dl_dict=dl_info,
                        out_dir=out_dir,
                        package_name=name,
                    )

                    # Update and save out cache
                    self.user_cache[url][dl_key].append(dl_info["full_name"])
                    save_json(self.user_cache,
                              self.user_cache_file,
                              sort_key="name",
                              )

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
            out_dir (str): Directory to save downloaded files
            package_name (str): Name of package to define subdirectories
                and keep track of links
        """

        package_id = None

        # Loop over download sites, hit the first one we find
        for dl_site in self.general_config["dl_sites"]:
            if dl_site in dl_dict:
                dl_links = dl_dict[dl_site]
                if len(dl_links) > 1:
                    self.logger.info(f"Multi-part file found for {dl_site}")

                for d in dl_links:
                    if "ouo" in d:
                        self.logger.info(f"Found shortened link {d}. Will bypass")
                        d_final = bypass_ouo(d, logger=self.logger)
                    else:
                        d_final = copy.deepcopy(d)

                    self.logger.info(f"Adding {d_final} to JDownloader")
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

                # Wait for a bit, since adding links can take a hot second
                time.sleep(5)

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
                                "Link offline, will remove and try with another download client"
                            )
                            any_offline = True
                            break

                if any_offline:
                    self.jd_device.linkgrabber.remove_links(package_ids=[package_id])
                    continue

                break

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
        self.logger.info("Beginning downloads")
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

        if package_id is None:
            raise ValueError(
                f"Did not find associated package with name {package_name}"
            )

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

        self.logger.info("Downloads complete")

        # And finally, cleanup
        self.jd_device.downloads.cleanup(
            action="DELETE_FINISHED",
            mode="REMOVE_LINKS_ONLY",
            selection_type="ALL",
            package_ids=[package_id],
        )

        self.logger.info("Cleanup complete")

        return True

    def clean_downloads(self):
        """Remove items from the cache and on disk, if needed"""

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
            for i, g in enumerate(games_to_delete):

                for dl_dir in DL_MAPPING:
                    g_dir = os.path.join(self.user_config["download_dir"], DL_MAPPING[dl_dir], g)
                    if os.path.exists(g_dir):
                        shutil.rmtree(g_dir)

                # And remove from the cache
                self.user_cache.pop(keys_to_delete[i])

        # Now, do a pass where we'll get rid of DLC/updates if they're no longer requested
        for key in ["dlc", "update"]:
            if not self.user_config[f"download_{key}"]:
                self.logger.info(f"Removing {key} from cache and disk")
                out_dir = os.path.join(self.user_config["download_dir"], DL_MAPPING[key])
                if os.path.exists(out_dir):
                    shutil.rmtree(out_dir)

                for d in self.user_cache:
                    self.user_cache[d].pop(key, [])

        # Save out the cache
        save_json(self.user_cache,
                  self.user_cache_file,
                  sort_key="name",
                  )

        return True
