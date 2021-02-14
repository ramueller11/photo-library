from www import app
from photolib import db, config


if __name__ == '__main__':
    db.connect(config.DB_PATH)
    app.run()



