from behave.__main__ import main as behave_main

if __name__ == "__main__":
    feature_file = "./features/1iwatch.feature"
    args = [feature_file]
    behave_main(args)
