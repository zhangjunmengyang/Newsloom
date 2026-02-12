"""Main pipeline orchestrator"""

import argparse
import yaml
import os
from pathlib import Path
from datetime import datetime, timezone

from sources.registry import SourceRegistry
from processors.fetcher import ParallelFetcher
from processors.filter import SmartFilter
from processors.generator import ReportGenerator
from utils.state import StateManager
from utils.time_utils import get_date_str


class Pipeline:
    """Main pipeline orchestrator for multi-source daily report"""

    def __init__(self, config_path: str = None):
        # Set default config path
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'

        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Initialize paths
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / 'data'
        self.reports_dir = Path(self.config['output']['base_dir'])

        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        """Load and process configuration"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        # Replace environment variables
        config = self._replace_env_vars(config)

        return config

    def _replace_env_vars(self, obj):
        """Recursively replace ${VAR} with environment variables"""
        if isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            return os.environ.get(var_name, '')
        else:
            return obj

    def run(self, layers: list = None, date_str: str = None):
        """
        Run the pipeline

        Args:
            layers: List of layers to run (fetch, filter, analyze, generate)
                   If None, runs all enabled layers
            date_str: Date string (YYYY-MM-DD), defaults to today
        """
        if layers is None:
            layers = self.config['pipeline']['enabled_layers']

        if date_str is None:
            date_str = get_date_str()

        print(f"\n🚀 Newsloom - Multi-Source Intelligence Pipeline")
        print(f"📅 Date: {date_str}")
        print(f"🔧 Layers: {', '.join(layers)}")
        print("=" * 60)

        # Initialize state manager
        state_file = self.base_dir / self.config['state']['file']
        dedup_window = self.config['state']['dedup_window_days']
        state_manager = StateManager(state_file, dedup_window)

        items = []

        # Layer 1: FETCH
        if 'fetch' in layers:
            print("\n" + "=" * 60)
            print("LAYER 1: FETCH")
            print("=" * 60)

            # Load sources
            sources_config_path = self.config_path.parent / 'sources.yaml'
            registry = SourceRegistry(str(sources_config_path))
            sources = registry.get_enabled_sources()

            if not sources:
                print("⚠️  No enabled sources found!")
                return

            # Fetch data
            fetcher = ParallelFetcher(sources, state_manager)
            hours_ago = self.config['pipeline']['fetch']['hours_ago']
            items = fetcher.fetch_all(hours_ago=hours_ago)

            # Save raw data
            raw_path = self.data_dir / 'raw' / f'{date_str}.jsonl'
            fetcher.save_raw_data(items, raw_path)

            # Save state
            state_manager.save()

        # Layer 2: FILTER
        if 'filter' in layers:
            print("\n" + "=" * 60)
            print("LAYER 2: FILTER")
            print("=" * 60)

            # Load items if not from fetch
            if not items:
                raw_path = self.data_dir / 'raw' / f'{date_str}.jsonl'
                if raw_path.exists():
                    fetcher = ParallelFetcher([], state_manager)
                    items = fetcher.load_raw_data(raw_path)
                else:
                    print(f"⚠️  No raw data found for {date_str}")
                    return

            # Load filter config
            filters_config_path = self.config_path.parent / 'filters.yaml'
            with open(filters_config_path) as f:
                filters_config = yaml.safe_load(f)

            # Filter items
            smart_filter = SmartFilter(filters_config)
            max_age_hours = self.config['pipeline']['filter']['max_age_hours']
            filtered_items = smart_filter.filter_items(items, max_age_hours)

            # Save filtered data
            filtered_path = self.data_dir / 'filtered' / f'{date_str}.jsonl'
            smart_filter.save_filtered_data(filtered_items, filtered_path)

            items = filtered_items

        # Layer 3: ANALYZE (will be implemented in Phase 3)
        if 'analyze' in layers:
            print("\n" + "=" * 60)
            print("LAYER 3: ANALYZE (Coming in Phase 3)")
            print("=" * 60)
            print("⚠️  AI analysis not yet implemented")
            # TODO: Implement in Phase 3

        # Layer 4: GENERATE
        if 'generate' in layers:
            print("\n" + "=" * 60)
            print("LAYER 4: GENERATE")
            print("=" * 60)

            # Load items if not from previous layers
            if not items:
                filtered_path = self.data_dir / 'filtered' / f'{date_str}.jsonl'
                if filtered_path.exists():
                    smart_filter = SmartFilter({})
                    items = smart_filter.load_filtered_data(filtered_path)
                else:
                    print(f"⚠️  No filtered data found for {date_str}")
                    return

            # Generate reports
            output_dir = self.reports_dir / date_str
            generator = ReportGenerator(self.config)
            generator.generate(items, date_str, output_dir)

            # Create 'latest' symlink
            latest_md = self.reports_dir / 'latest.md'
            latest_html = self.reports_dir / 'latest.html'

            if (output_dir / 'report.md').exists():
                if latest_md.exists() or latest_md.is_symlink():
                    latest_md.unlink()
                latest_md.symlink_to(output_dir / 'report.md')

            if (output_dir / 'report.html').exists():
                if latest_html.exists() or latest_html.is_symlink():
                    latest_html.unlink()
                latest_html.symlink_to(output_dir / 'report.html')

        print("\n" + "=" * 60)
        print("✅ Pipeline completed successfully!")
        print("=" * 60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Newsloom - Multi-Source Intelligence Pipeline'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config.yaml (default: config/config.yaml)'
    )

    parser.add_argument(
        '--layers',
        type=str,
        help='Comma-separated layers to run (fetch,filter,analyze,generate)'
    )

    parser.add_argument(
        '--date',
        type=str,
        help='Date string YYYY-MM-DD (default: today)'
    )

    args = parser.parse_args()

    # Parse layers
    layers = None
    if args.layers:
        layers = [layer.strip() for layer in args.layers.split(',')]

    # Run pipeline
    pipeline = Pipeline(config_path=args.config)
    pipeline.run(layers=layers, date_str=args.date)


if __name__ == '__main__':
    main()
