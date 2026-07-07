from china_cars.export_excel import export_workbook
from china_cars.pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline()
    export_path = export_workbook()
    print(f"Pipeline concluido. Excel gerado em: {export_path}")

