import tomllib

with open(".secrets.toml", "rb") as s:
    secrets = tomllib.load(s)
    print(secrets["API_KEY"])
