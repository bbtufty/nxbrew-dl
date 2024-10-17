from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import QTableWidgetItem, QHeaderView

COLOURS = {
    "green": QColor(0, 175, 0, 255),
    "orange": QColor(255, 170, 0, 255),
    "red": QColor(175, 0, 0, 255),
}


def set_dl(
    table,
    row_position,
):
    """Set downloaded state for each row

    Args:
        table (QTableWidget): QTableWidget
        row_position (int): Row position
    """

    dl = QTableWidgetItem()
    dl.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
    dl.setCheckState(Qt.CheckState.Unchecked)

    table.setItem(row_position, 1, dl)


class TableRowWidget(QTableWidgetItem):

    def __init__(self, row_dict, row_name_key="long_name"):
        """Custom table rows, that include pretty colour and useful columns

        Args:
            row_dict (dict): Dictionary of row details
            row_name_key (str): Column name to define the name for the row
        """
        super(TableRowWidget, self).__init__()

        self.name = row_dict[row_name_key]
        self.url = row_dict["url"]

        # If we've parsed neither an NSP or XCI, mark as undefined
        if not row_dict["has_nsp"] and not row_dict["has_xci"]:
            row_dict["has_nsp"] = "UNDEF"
            row_dict["has_xci"] = "UNDEF"

        self.row_dict = row_dict
        self.row_name_key = row_name_key

    def setup_row(self, table, row_position):
        """Create a row for a ROM with all the relevant info

        Args:
            table (QTableWidget): QTableWidget
            row_position (int): Row position
        """

        self.set_name(
            table=table,
            row_position=row_position,
        )

        set_dl(
            table=table,
            row_position=row_position,
        )

        # Set NSP/XCI
        self.set_filetype(
            table=table,
            key="has_nsp",
            row_position=row_position,
            column_position=2,
        )
        self.set_filetype(
            table=table,
            key="has_xci",
            row_position=row_position,
            column_position=3,
        )
        self.set_filetype(
            table=table,
            key="has_update",
            row_position=row_position,
            column_position=4,
        )
        self.set_filetype(
            table=table,
            key="has_dlc",
            row_position=row_position,
            column_position=5,
        )

        # Finally, resize the table. Shrink everything but title to minimum
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # And stretch out the title to fill the rest
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

    def set_name(
        self,
        table,
        row_position,
    ):
        """Set the name for the row

        Args:
            table (QTableWidget): Table widget
            row_position (int): Position of the row to set name for
        """

        item = QTableWidgetItem(self.name)
        item.setToolTip(self.url)

        table.setItem(row_position, 0, item)

    def set_filetype(
        self,
        table,
        key,
        row_position,
        column_position,
    ):
        """Set the status of a filetype

        If a key evaluates to true in the row_dict, it will set
        a text box that says "Yes" and is green. Otherwise, will
        be a red "No"

        Args:
            table (QTableWidget): Table widget
            key (str): Key to check
            row_position (int): Row position
            column_position (int): Column position for the key
        """

        has_filetype = QTableWidgetItem()
        has_filetype.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set text and colour
        if self.row_dict[key] == "UNDEF":
            has_filetype.setText("???")
            colour = QBrush(COLOURS["orange"])
        elif self.row_dict[key]:
            has_filetype.setText("Yes")
            colour = QBrush(COLOURS["green"])
        else:
            has_filetype.setText("No")
            colour = QBrush(COLOURS["red"])

        colour.setStyle(Qt.BrushStyle.SolidPattern)
        has_filetype.setBackground(colour)

        has_filetype.setFlags(Qt.ItemFlag.ItemIsEnabled)

        table.setItem(row_position, column_position, has_filetype)
