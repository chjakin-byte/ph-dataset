import argparse
from app.runner import PipelineRunner
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Kickstarter Research Pipeline")
    parser.add_argument("--config", type=str, required=True, help="Path to configuration YAML file")
    
    args = parser.parse_args()
    
    try:
        runner = PipelineRunner(args.config)
        runner.run()
    except Exception as e:
        logger.error(f"Execution failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
