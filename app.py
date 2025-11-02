from src.utils.logger import get_logger
from src.utils.scrape_webpage import scrape_all


logger = get_logger(__name__)


def main():
    logger.info("Hello from 30daymapchallenge!")
    scrape_all("nsmc_events.csv", "https://seismic.pmd.gov.pk/events.php")
    logger.info("Done — output written to nsmc_events.csv")


if __name__ == "__main__":
    main()
