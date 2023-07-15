from behave.__main__ import main as behave_main

if __name__ == "__main__":
    feature_file = "./features/twinning_1st_time.feature"
    args = ["--define", f"iterations=100", feature_file]
    behave_main(args)
