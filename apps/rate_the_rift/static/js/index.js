// This will be the object that will contain the Vue attributes
// and be used to initialize it.
let app = {};
var users = [];
var filtered_users = [];
var text = "";
var meow_text = "";
var meows = [];
var your_feed_is_active = true;
var your_meows_is_active = false;
var recent_meows_is_active = false;
var active_user = ""
var reply_id = -1
var reply_text = ""
var reply_meow = null
// Given an empty app object, initializes it filling its attributes,
// creates a Vue instance, and then initializes the Vue instance.
let init = (app) => {
  // This is the Vue data.
  app.data = {
    users: users,
    text: text,
    filtered_users: filtered_users,
    meows: meows,
    meow_text: meow_text,
    your_feed_is_active: your_feed_is_active,
    your_meows_is_active: your_meows_is_active,
    recent_meows_is_active: recent_meows_is_active,
    active_user: active_user,
    reply_id: reply_id,
    reply_text: reply_text,
    reply_meow: reply_meow
  };

  
  app.enumerate = (a) => {
      // This adds an _idx field to each element of the array.
      let k = 0;
      a.map((e) => {
          e._idx = k++;
        });
        return a;
    };
    
    // This contains all the methods.
    app.methods = {};

    // Helper function to set booleans for your_feed, your_meows, and recent_meows
    app.methods.set_active = function (active) {
      if (active == "your_feed") {
        app.data.your_feed_is_active = true;
        app.data.your_meows_is_active = false;
        app.data.recent_meows_is_active = false;
        app.data.active_user = "";
      } else if (active == "your_meows") {
        app.data.your_feed_is_active = false;
        app.data.your_meows_is_active = true;
        app.data.recent_meows_is_active = false;
        app.data.active_user = "";
      } else if (active == "recent_meows") {
        app.data.your_feed_is_active = false;
        app.data.your_meows_is_active = false;
        app.data.recent_meows_is_active = true;
        app.data.active_user = "";
      } else {
        app.data.your_feed_is_active = false;
        app.data.your_meows_is_active = false;
        app.data.recent_meows_is_active = false;
        app.data.active_user = active;
      }
    };

  app.methods.get_users = function () {
    axios.get(get_users_url).then(function (r) {
      app.data.users = app.enumerate(r.data.users);
    });
  };

  // "Your Feed" implementation
  app.methods.get_meows = function () {
    axios
      .get("../get_meows")
      .then(function (r) {
        // Enumerates and sets meows
        app.data.meows = app.enumerate(r.data.meows);
        app.methods.set_active("your_feed");
      })
      .then(function (r) {
        // Uses Sugar.Date().relative to set timestamps to human readable format
        app.data.meows.forEach(function (meow) {
          meow.timestamp = Sugar.Date(meow.timestamp + "Z").relative();
        });
      });
  };

  // "Your Meows" implementation
  app.methods.get_your_meows = function () {
    axios
      .get("../get_your_meows")
      .then(function (r) {
        // Enumerates and sets meows
        app.data.meows = app.enumerate(r.data.meows);
        app.methods.set_active("your_meows");
      })
      .then(function (r) {
        // Uses Sugar.Date().relative to set timestamps to human readable format
        app.data.meows.forEach(function (meow) {
          meow.timestamp = Sugar.Date(meow.timestamp + "Z").relative();
        });
      });
  };

  // "Recent Meows" implementation
  app.methods.get_recent_meows = function () {
    axios
      .get("../get_recent_meows")
      .then(function (r) {
        // Enumerates and sets meows
        app.data.meows = app.enumerate(r.data.meows);
        app.methods.set_active("recent_meows");
      })
      .then(function (r) {
        // Uses Sugar.Date().relative to set timestamps to human readable format
        app.data.meows.forEach(function (meow) {
          meow.timestamp = Sugar.Date(meow.timestamp + "Z").relative();
        });
      });
  };

  // "Recent Meows" implementation
  app.methods.get_user_meows = function (user) {
    axios
      .get("../get_user_meows/" + user.id)
      .then(function (r) {
        // Enumerates and sets meows
        app.data.meows = app.enumerate(r.data.meows);
        app.methods.set_active(user.username);
      })
      .then(function (r) {
        // Uses Sugar.Date().relative to set timestamps to human readable format
        app.data.meows.forEach(function (meow) {
          meow.timestamp = Sugar.Date(meow.timestamp + "Z").relative();
        });
      });
  };



  app.methods.set_follow = function (user) {
    axios
      .post(follow_url, {
        user_id: user.id,
        follow: !user.followed,
        username: user.username,
      })
      .then(function (r) {
        app.methods.get_users();
      })
      .then(function (r) {
        app.methods.get_meows();
      });
  };

  app.methods.post_meow = function () {
    axios
      .post(post_meow_url, { meow_text: app.data.meow_text })
      .then(function (r) {
        app.methods.get_meows();
      });
  };

  app.methods.remeow = function (author, content) {
    axios
      .post(post_meow_url, { meow_text: "RT " + author + ": " + content })
      .then(function (r) {
        app.methods.get_meows();
      });
    };

  app.methods.filter_users = function (text) {
    // Filter users by username using JS
    app.data.filtered_users = app.data.users.filter((user) =>
      user.username.includes(app.data.text)
    );
  };

  app.methods.show_reply = function (meow_id) {
    app.data.reply_id = meow_id

    // Set reply_meow to the meow with meow.id == meow_id if necessary
    if (app.data.reply_meow == null || app.data.reply_meow.id != meow_id) {
        app.data.reply_meow = app.data.meows.find((meow) => meow.id == meow_id);
    } else {
        app.data.reply_meow.replies += 1;
    }

    // Send request to get replies
    axios
        .get("../get_replies/" + meow_id)
        .then(function (r) {
            app.data.meows = app.enumerate(r.data.replies);
        }).then(function (r) { 
            app.data.meows.forEach(function (reply) {
                reply.timestamp = Sugar.Date(reply.timestamp + "Z").relative();
            });
        }
        );
    };

    app.methods.post_reply = function () {
        axios
      .post(post_reply_url, { reply_text: app.data.reply_text, parent_id: app.data.reply_id })
      .then(function (r) {
        app.methods.show_reply(app.data.reply_id);
      });
    };


  // This creates the Vue instance.
  app.vue = new Vue({
    el: "#vue-target",
    data: app.data,
    methods: app.methods,
  });

  // And this initializes it.
  app.init = () => {
    app.methods.get_users();
    app.methods.get_meows();
  };

  // Call to the initializer.
  app.init();
};

// This takes the (empty) app object, and initializes it,
// putting all the code in it.
init(app);