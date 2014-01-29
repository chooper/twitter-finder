twitter-finder is a bot that searches twitter for a set of search terms and then
publishes metrics based on when those terms are found.

It runs well on Linux but it should run just as well on Mac OSX or
Windows.

# Installation

## Heroku

1. Check the code out of git: `git clone git@github.com:chooper/twitter-finder.git`
2. Create a [Heroku](http://www.heroku.com) app: `heroku create`
3. Go to [Twitter's Developer page](https://dev.twitter.com/apps) and create a new application
4. Set up your database and configure your Heroku app with the Oauth credentials twitter gave you

   ```
   heroku addons:add heroku-postgresql:standard-yanari
   heroku pg:wait
   heroku pg:credentials
   heroku config:set DATABASE_URL=... \
     TW_USERNAME=<twitter username> \
     TW_CONSUMER_KEY=... \
     TW_CONSUMER_SECRET=... \
     TW_ACCESS_TOKEN=... \
     TW_ACCESS_TOKEN_SECRET=... \
     DEBUG=true
   ```
5. Push your application: `git push heroku master`
6. Test that your finder works: `heroku run ./finder.py`
7. Scale it to 1: `heroku ps:scale worker=1`

That should be it! It seems like alot of steps but after this you're all done!

## Traditional (Linux)

Sorry, but these steps are mostly untested and written from memory. Please send
me a pull request if you find a mistake.

1. Check the code out of git: `git clone git@github.com:chooper/twitter-finder.git`
2. Go to [Twitter's Developer page](https://dev.twitter.com/apps) and create a new application
3. Configure your repeater app with the Oauth credentials twitter gave you
    1. `cp .env.sample .env` and fill in the environment variables
4. Install dependencies (consider a virtualenv): `pip install -r requirements.txt`
5. Test that it works: `source .env ; ./repeater.py`

