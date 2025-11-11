import xml.etree.ElementTree as ET
import pandas as pd
import sys
import argparse


def extract_parameter_values(xml_file, parameter_key, board):
    global_param_values = []
    channel_param_values = []

    parameters = board.find("parameters")
    if parameters is not None:
        for entry in parameters.findall("entry"):
            key = entry.find("key")
            if key is not None and key.text == parameter_key:
                value_elem = entry.find("value")
                if value_elem is not None:
                    value_value = value_elem.find("value")
                    if value_value is not None:
                        global_param_values.append(value_value.text)

    channels = board.findall("channel")
    for channel in channels:
        channelkey = channel.find("index")
        if channelkey is not None:
            values = channel.find("values")
            if values is not None:
                for entry in values.findall("entry"):
                    key = entry.find("key")
                    if key is not None and key.text == parameter_key:
                        value_element = entry.find("value")
                        if value_element is not None:
                            channel_param_values.append(
                                (channelkey.text, value_element.text)
                            )

    return global_param_values, channel_param_values


def format_coarse_gain(value):
    """Format coarse gain values"""
    if value.startswith("COARSE_GAIN_"):
        # Extract the multiplier (e.g., "X4" -> "4")
        multiplier = value.replace("COARSE_GAIN_X", "")
        return f"{multiplier}x"
    return value


def build_table(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Updated parameter keys to match actual XML structure
    parameter_keys = {
        "SRV_PARAM_CH_COARSE_GAIN": "Coarse gain",
        "SRV_PARAM_CH_ENERGY_FINE_GAIN": "Fine gain",
        "SRV_PARAM_CH_PRETRG": "Pre-trigger [ns]",
        "SRV_PARAM_CH_THRESHOLD": "Trigger threshold [ADC]",
        "SRV_PARAM_RECLEN": "Record length [ns]",
        "SRV_PARAM_CH_POLARITY": "Polarity",
        "SRV_PARAM_CH_TRAP_TRISE": "Trap rise time [ns]",
        "SRV_PARAM_CH_TRAP_TFLAT": "Trap flat top [ns]",
        "SRV_PARAM_CH_TRAP_PEAKING": "Trap peaking time [%]",
    }

    all_boards_data = {}

    for board_idx, board in enumerate(root.findall("board")):
        # Check if board is active/connected
        connected = board.find("connected")
        active = board.find("active")

        if (
            connected is None
            or connected.text != "true"
            or active is None
            or active.text != "true"
        ):
            continue

        # Get board info
        board_id_elem = board.find("id")
        board_model_elem = board.find("modelName")
        board_id = (
            board_id_elem.text if board_id_elem is not None else f"Board_{board_idx}"
        )
        board_model = (
            board_model_elem.text if board_model_elem is not None else "Unknown"
        )

        # Get channel count
        channel_count_elem = board.find("channelCount")
        channel_count = (
            int(channel_count_elem.text) if channel_count_elem is not None else 16
        )

        channels = [f"CH{i}" for i in range(channel_count)]
        data = {
            row_name: {channel: None for channel in channels}
            for row_name in parameter_keys.values()
        }

        # Populate data for all channels
        for parameter_key, row_name in parameter_keys.items():
            globalvalues, chvalues = extract_parameter_values(
                xml_file, parameter_key, board
            )

            global_value = globalvalues[0] if globalvalues else None

            # Format specific parameters
            if parameter_key == "SRV_PARAM_CH_COARSE_GAIN" and global_value:
                global_value = format_coarse_gain(global_value)

            # Set global value for all channels
            for channel in channels:
                data[row_name][channel] = global_value

            # Override with channel-specific values
            for channelkey, value in chvalues:
                if parameter_key == "SRV_PARAM_CH_COARSE_GAIN":
                    value = format_coarse_gain(value)
                channel_name = f"CH{channelkey}"
                if channel_name in channels:
                    data[row_name][channel_name] = value

        # Convert to DataFrame and store
        df = pd.DataFrame(data).T
        if not df.empty:
            board_label = f"{board_model} ({board_id})"
            all_boards_data[(board_idx, board_label)] = df

    return all_boards_data


def print_filtered_output(all_boards_data, board_filter=None, channel_filter=None):
    """
    Print boards and channels based on filters.

    Args:
        all_boards_data: Dictionary with (board_idx, board_label) as keys and DataFrames as values
        board_filter: Board index to filter (None = all boards)
        channel_filter: List of channel numbers to filter (None = all channels)
    """
    if not all_boards_data:
        print("\nNo active boards found.")
        return

    for (board_idx, board_label), df in all_boards_data.items():
        # Skip board if not matching filter
        if board_filter is not None and board_idx != board_filter:
            continue

        # Filter channels if specified
        if channel_filter is not None:
            channel_names = [f"CH{ch}" for ch in channel_filter]
            # Only keep channels that exist in the dataframe
            available_channels = [ch for ch in channel_names if ch in df.columns]
            if not available_channels:
                print(f"\n{board_label}:")
                print(
                    f"  Warning: Requested channels {channel_filter} not found in this board."
                )
                continue
            df_display = df[available_channels]
        else:
            df_display = df

        print(f"\n{board_label}:")
        print(df_display)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract CoMPASS settings from XML file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        # Show all boards and channels
        python MUSIC-getCoMPASS.py settings.xml

        # Show only board 0
        python MUSIC-getCoMPASS.py settings.xml --board 0

        # Show only channels 3 and 11 from all boards
        python MUSIC-getCoMPASS.py settings.xml --channels 3 11

        # Show channels 3 and 11 from board 0 only
        python MUSIC-getCoMPASS.py settings.xml --board 0 --channels 3 11
        """,
    )

    parser.add_argument("xml_file", help="Path to CoMPASS settings.xml file")
    parser.add_argument(
        "--board",
        "-b",
        type=int,
        default=None,
        help="Board index to display (0-based). If not specified, shows all boards.",
    )
    parser.add_argument(
        "--channels",
        "-c",
        type=int,
        nargs="+",
        default=None,
        help="Channel number(s) to display. If not specified, shows all channels.",
    )

    args = parser.parse_args()

    print("Filename: " + args.xml_file)
    all_boards_data = build_table(args.xml_file)

    # Print with filters
    print_filtered_output(all_boards_data, args.board, args.channels)
