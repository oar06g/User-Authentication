import scripts.migrate
scripts.migrate.setup()

if __name__ == "__main__":
    from src import run
    run()

# ngrok http --url=skilled-tuna-skilled.ngrok-free.app 8000