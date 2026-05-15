import json

import yaml


class DumperEdit(yaml.Dumper):
    """Custom formatting for yaml"""

    def increase_indent(self, flow=False, indentless=False):
        return super(DumperEdit, self).increase_indent(flow, False)

    def write_line_break(self, data=None):
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()


def load_yml(f):
    """Load YAML file

    Args:
        f (str): Path to YAML file
    """

    with open(f, "r") as file:
        config = yaml.safe_load(file)

    return config


def save_yml(f, data):
    """Save YAML file

    Args:
        f (str): Path to YAML file
        data (dict): Data to be saved
    """

    with open(f, "w") as file:
        yaml.dump(
            data,
            file,
            Dumper=DumperEdit,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
        )


def load_json(file):
    """Load json file

    Args:
        file (str): Path to JSON file
    """

    with open(file, "r", encoding="utf-8") as f:
        j = json.load(f)

    return j


def save_json(data, out_file, sort_key=None):
    """Save json in a pretty way

    Args:
        data (dict): Data to be saved
        out_file (str): Path to JSON file
        sort_key (str): Key within each dictionary entry to
            sort by. Default is None, which will not sort.
    """

    # Optionally sort this by name
    if sort_key is not None:

        sort_data = True

        # Check this key exists for every entry
        sort_key_values = [data[key].get(sort_key, False) for key in data]
        if any(not k for k in sort_key_values):
            sort_data = False

        if sort_data:
            data = dict(sorted(data.items(), key=lambda i: i[-1][sort_key]))

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=4,
        )
