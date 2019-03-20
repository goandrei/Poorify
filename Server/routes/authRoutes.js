const passport = require('passport');

module.exports = (app) => {
    //when the user accesses '/auth/google', gets kicked into the OAuth flow, with the strategy google (Google OAauth) 
    app.get(
        '/auth/google', 
        passport.authenticate('google', {
            scope: ['profile', 'email'] //we want access to profile information and user email
        })
    );

    //after the user gives permission, it gets redirected to '/auth/google/callback' and passport handles the rest
    app.get(
        '/auth/google/callback',
        passport.authenticate('google'),
        (req, res) => {
            res.redirect('/api/current_user')
        }
    );
    
    // routes for logout
    app.get('/api/logout', (req, res) => {
        req.logout();
        var s = `You have logged out successfully.`;
        res.send(s);
    });

    app.get(
        '/api/current_user',
        (req, res) => {
            if(req.user){
                var s = ` Login successful, welcome ${req.user.name} ! `;
            }else{
                var s = `You are not logged in !`;
            }
            res.send(s);
        }
    );

    app.get(
        '/',
        (req, res) => {
            res.send('HOME PAGE')
        }
    );
}