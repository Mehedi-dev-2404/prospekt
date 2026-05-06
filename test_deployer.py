import asyncio

from pipeline.deployer import deploy_landing_page


def main() -> None:
    with open("test_output.html", "r", encoding="utf-8") as f:
        html = f.read()

    url = asyncio.run(deploy_landing_page("Brick Lane Dental Studio", html))
    print(url)


if __name__ == "__main__":
    main()
