import argparse
import dataclasses
import sys

from .config import ConfigError, load_config


def main(argv=None):
    p = argparse.ArgumentParser(prog="vlbapipe")
    sub = p.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="run calibration/imaging stages")
    run.add_argument("config")
    run.add_argument("--stages", help="comma-separated stage names (default: all)")
    run.add_argument("--export-script", metavar="PATH",
                     help="write the CASA calls made during the run to PATH")

    gen = sub.add_parser("generate",
                         help="write a standalone CASA script (scriptForCalibration style)")
    gen.add_argument("config")
    gen.add_argument("-o", "--output", metavar="PATH",
                     help="script path (default: scriptForCalibration_<vis>.py)")
    gen.add_argument("--refant", help="override the config's refant (needed if it is 'auto')")
    args = p.parse_args(argv)

    if args.cmd == "generate":
        from .scriptgen import write_script

        try:
            config = load_config(args.config)
            if args.refant:
                config = dataclasses.replace(config, refant=args.refant)
            out = args.output or f"scriptForCalibration_{config.vis_pre}.py"
            path = write_script(config, out, source=args.config)
        except ConfigError as e:
            sys.exit(str(e))
        print(f"Wrote {path}\nRun with: casa --nologger --nogui -c {path} [--steps 0-17]")
        return

    from .pipeline import Pipeline  # needs CASA only when actually running

    pipe = Pipeline.from_yaml(args.config)
    pipe.run(args.stages.split(",") if args.stages else None)
    if args.export_script:
        pipe.export_script(args.export_script)
