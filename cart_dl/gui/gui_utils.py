from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QListWidgetItem

from ..gui.custom_widgets import TableRowWidget


@Slot()
def open_url(url):
    """Opens a URL"""

    QDesktopServices.openUrl(url)


def add_row_to_table(
        table,
        row_dict,
        row_name_key="long_name",
):
    """Add row to table, using a dictionary of important info

    Args:
        table (QTableWidget): Table to add row to
        row_dict (dict): Dictionary of data for the row
        row_name_key (str): Key used to identify the name for the row.
            Defaults to "long_name"
    """

    row_position = table.rowCount()

    table.insertRow(row_position)

    row = TableRowWidget(
        row_dict,
        row_name_key=row_name_key,
    )
    row.setup_row(
        table=table,
        row_position=row_position,
    )

    return row


def add_item_to_list(item_list, item_name, check_state=None):
    """Add item to list widget, optionally setting a check state

    Args:
        item_list (QListWidgetItem): Item to add
        item_name (str): Item name
        check_state (None, True, False): If None, will not set check
            state. Otherwise, will set checked (True) or not checked
            (False). Defaults to None
    """

    item = QListWidgetItem(item_list)
    item.setText(item_name)
    if check_state is not None:
        if not check_state:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    return item


def set_ordered_list(
        list_widget,
        item_dict,
        items,
):
    """Set checked items from an ordered list

    Args:
        list_widget (QListWidget): The QListWidget
        item_dict (dict): A dictionary of items that contains the list items to index
        items (list): A list of items to set checked, in order
    """

    # Set the items to checked
    for i in items:
        item_dict[i]["item"].setCheckState(Qt.CheckState.Checked)
        item_dict[i]["check_state"] = True

    # Move the items into order
    for i in items[::-1]:
        idx = list_widget.row(item_dict[i]["item"])
        take_item = list_widget.takeItem(idx)
        list_widget.insertItem(0, take_item)
        list_widget.setCurrentRow(0)

    return True


def get_ordered_list(
        list_widget,
):
    """Get checked items from an ordered list"""

    n_items = list_widget.count()

    items = []

    for i in range(n_items):

        # Get item name, and check state
        item = list_widget.item(i)
        item_name = item.text()
        check_state = item.checkState()

        if check_state == Qt.CheckState.Checked:
            items.append(item_name)

    return items
