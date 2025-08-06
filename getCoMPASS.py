import xml.etree.ElementTree as ET
import pandas as pd
import sys


def extract_parameter_values(xml_file, parameter_key, board):
    global_param_values = []
    channel_param_values = []

    parameters = board.find("parameters")
    for entry in parameters.findall("entry"):
        key = entry.find("key").text
        if key == parameter_key:
            value = entry.find("value").find("value").text
            global_param_values.append(value)

    channels = board.findall("channel")
    for channel in channels:
        channelkey = channel.find("index").text
        values = channel.find("values")
        for entry in values.findall("entry"):
            key = entry.find("key").text
            if key == parameter_key:
                value_element = entry.find("value")
                if value_element is not None:
                    value = value_element.text
                    channel_param_values.append((channelkey, value))

    return global_param_values, channel_param_values


def format_energy_coarse_gain(value):
    if value.startswith("CHARGESENS_") and "FC_LSB_VPP" in value:
        parts = value.split("_")
        gain_value = parts[1]
        return f"{gain_value}"
    return value


def build_table(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    parameter_keys = {
        "SRV_PARAM_CH_INDYN": "Input dynamic range [Vpp]",
        "SRV_PARAM_CH_ENERGY_COARSE_GAIN": "Energy coarse gain [fC/LSB x Vpp]",
        "SRV_PARAM_CH_GATE": "Gate [ns]",
        "SRV_PARAM_CH_GATESHORT": "Short gate [ns]",
        "SRV_PARAM_CH_GATEPRE": "Pre-gate [ns]",
        "SRV_PARAM_CH_DISCR_MODE": "Trigger mode",
        "SRV_PARAM_CH_THRESHOLD": "Trigger threshold [ADC]",
        "SRV_PARAM_RECLEN": "Record length [ns]",
    }

    all_boards_data = {}

    for board_idx, board in enumerate(root.findall("board")):
        channel_count = 8
        channels = [f"CH{i}" for i in range(channel_count)]
        data = {
            row_name: {channel: None for channel in channels}
            for row_name in parameter_keys.values()
        }

        # Identify enabled channels for this board
        enabled_channels = set()
        _, enabled_values = extract_parameter_values(
            xml_file, "SRV_PARAM_CH_ENABLED", board
        )
        for channelkey, value in enabled_values:
            if value == "true":
                enabled_channels.add(f"CH{channelkey}")

        # Skip board if no channels are enabled
        if not enabled_channels:
            continue

        # Populate data for enabled channels
        for parameter_key, row_name in parameter_keys.items():
            globalvalues, chvalues = extract_parameter_values(
                xml_file, parameter_key, board
            )

            global_value = globalvalues[0] if globalvalues else None
            if parameter_key == "SRV_PARAM_CH_ENERGY_COARSE_GAIN" and global_value:
                global_value = format_energy_coarse_gain(global_value)

            for channel in channels:
                if channel in enabled_channels:
                    data[row_name][channel] = global_value

            for channelkey, value in chvalues:
                if parameter_key == "SRV_PARAM_CH_ENERGY_COARSE_GAIN":
                    value = format_energy_coarse_gain(value)
                channel_name = f"CH{channelkey}"
                if channel_name in enabled_channels:
                    data[row_name][channel_name] = value

        # Filter out disabled channels
        for row_name in data.keys():
            data[row_name] = {
                k: v for k, v in data[row_name].items() if k in enabled_channels
            }

        # Convert to DataFrame and store only if there are enabled channels
        df = pd.DataFrame(data).T
        if not df.empty and df.columns.size > 0:
            all_boards_data[f"Board_{board_idx}"] = df

    return all_boards_data


if __name__ == "__main__":
    xml_file = sys.argv[1]
    print("Filename: " + xml_file)
    output = build_table(xml_file)

    if not output:
        print("\nNo boards with enabled channels found.")
    else:
        for board_name, df in output.items():
            print(f"\n{board_name}:")
            print(df)
