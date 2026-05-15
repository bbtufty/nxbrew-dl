import copy
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

import cart_dl
from .gui_utils import set_ordered_list, add_item_to_list
from .layout_regions_languages import Ui_FormRegionsLanguages
from ..util import load_yml


class RegionLanguageWindow(QWidget):

    def __init__(
        self,
        user_config=None,
        general_config=None,
        parent=None,
    ):
        """cart-dl region/language window

        This part controls the advanced region/language options,
        where order is important and there are quite a few options!

        Args:
            user_config (dict): user config. If None, will
                load in from expected path
            general_config (dict): general config. If None,
                will load in from expected path
        """

        super().__init__()

        self.ui = Ui_FormRegionsLanguages()
        self.ui.setupUi(self)

        # Read in the general config
        self.mod_dir = os.path.dirname(cart_dl.__file__)
        general_config_filename = os.path.join(self.mod_dir, "configs", "general.yml")
        if general_config is None:
            general_config = load_yml(general_config_filename)
        self.general_config = copy.deepcopy(general_config)

        # Read in the user config
        user_config_file = os.path.join(os.getcwd(), "config.yml")
        if user_config is None:
            if os.path.exists(user_config_file):
                user_config = load_yml(user_config_file)
            else:
                user_config = {}
        self.user_config = copy.deepcopy(user_config)

        self.region_items = {}
        self.language_items = {}

    def load_config(self):
        """Load the region/language configuration"""

        # Set regions, but only if the dictionary's empty
        if not self.region_items:
            self.region_items = self.populate_list(
                "regions",
                self.ui.listWidgetConfigRegionsLanguagesRegions,
                check_state=False,
            )

            # Set default regions, if not in the config file
            if "regions" not in self.user_config:
                self.populate_list(
                    "default_selected_regions",
                    self.ui.listWidgetConfigRegionsLanguagesRegions,
                    item_dict=self.region_items,
                    check_state=True,
                )

            self.set_regions()

        # Set languages, but only if the dictionary's empty
        if not self.language_items:
            self.language_items = self.populate_list(
                "languages",
                self.ui.listWidgetConfigRegionsLanguagesLanguages,
                check_state=False,
            )

            # Set default languages, if not in the config file
            if "languages" not in self.user_config:
                self.populate_list(
                    "default_selected_languages",
                    self.ui.listWidgetConfigRegionsLanguagesLanguages,
                    item_dict=self.language_items,
                    check_state=True,
                )

            self.set_languages()

    def populate_list(
        self,
        default_config_key,
        list_widget,
        item_dict=None,
        check_state=None,
    ):
        """Load items from a dict, potentially checked/unchecked"""

        if item_dict is None:
            item_dict = {}

        all_keys = self.general_config[default_config_key]

        for key in all_keys:

            if key not in item_dict:
                item = add_item_to_list(
                    list_widget,
                    self.tr(key),
                    check_state=check_state,
                )
            else:
                item = item_dict[key]["item"]
                if check_state is not None:
                    if not check_state:
                        item.setCheckState(Qt.CheckState.Unchecked)
                    else:
                        item.setCheckState(Qt.CheckState.Checked)

            item_dict[key] = {
                "item": item,
                "check_state": check_state,
            }

        return item_dict

    def set_regions(self):
        """Set regions from the user config"""

        if "regions" not in self.user_config:
            return False

        # Set up the region list
        regions = self.user_config["regions"]
        set_ordered_list(
            self.ui.listWidgetConfigRegionsLanguagesRegions,
            item_dict=self.region_items,
            items=regions,
        )

    def set_languages(self):
        """Set languages from the user config"""

        if "languages" not in self.user_config:
            return False

        # Set up the language list
        languages = self.user_config["languages"]
        set_ordered_list(
            self.ui.listWidgetConfigRegionsLanguagesLanguages,
            item_dict=self.language_items,
            items=languages,
        )
