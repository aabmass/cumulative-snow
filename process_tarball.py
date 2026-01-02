import logging
import polars as pl
import tarfile
import argparse

logging.basicConfig(level=logging.INFO)


def tar_to_parquet(tar_path, output_path):
    frames = []
    logging.info("Opening %s tar file", tar_path)
    with tarfile.open(tar_path, "r|gz") as tar:
        logging.info("Done opening %s tar file", tar_path)
        for member in tar:
            logging.info("Got file: %s", member.name)
            if member.name.endswith(".csv"):
                # Stream the file directly into a Polars DataFrame
                f = tar.extractfile(member)
                if f is not None:
                    logging.info("Processing file: %s", member.name)
                    frames.append(pl.read_csv(f))
                else:
                    logging.warning("Skipping empty file: %s", member.name)

    # Combine all CSVs into one and save as Parquet
    full_df = pl.concat(frames)
    full_df.write_parquet(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert a tarball of CSVs to a single Parquet file."
    )
    parser.add_argument(
        "tar_path", help="Path to the input tar.gz file containing CSVs."
    )
    parser.add_argument("output_path", help="Path to the output Parquet file.")
    parser.add_argument(
        "--log_level",
        help="Set the logging level (e.g., INFO, DEBUG, WARNING).",
        default="INFO",
    )

    args = parser.parse_args()
    # logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    tar_to_parquet(args.tar_path, args.output_path)
