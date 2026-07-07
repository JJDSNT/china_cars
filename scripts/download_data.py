from china_cars.download import download_all


if __name__ == "__main__":
    files = download_all()
    for item in files:
        print(f"{item.status}: {item.path}")

