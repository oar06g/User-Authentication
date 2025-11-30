"""Main entry point for User Authentication System"""
# import scripts.migrate

# Setup database and migrations
# scripts.migrate.setup()

if __name__ == "__main__":
    from src import run
    run()