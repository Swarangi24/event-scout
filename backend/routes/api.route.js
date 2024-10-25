const router = require('express').Router();
const { google } = require('googleapis');
const mongoose = require('mongoose');

// MongoDB connection
mongoose.connect('mongodb://localhost:27017/eventdb', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Define a User schema
const userSchema = new mongoose.Schema({
  email: String,
  accessToken: String,
  refreshToken: String,
  scope: String,
  tokenType: String,
  expiryDate: Number,
});

// Create a User model
const User = mongoose.model('User', userSchema);

const GOOGLE_CLIENT_ID = '912370917797-c08nfe40bnvl9qog13uml20n2gieqhea.apps.googleusercontent.com';
const GOOGLE_CLIENT_SECRET = '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';
const oauth2client = new google.auth.OAuth2(
  GOOGLE_CLIENT_ID,
  GOOGLE_CLIENT_SECRET,
  'http://localhost:3000'
);

router.get('/', async (req, res, next) => {
  res.send({ message: 'Ok, API is working 🚀' });
});
router.post('/create-token', async (req, res, next) => {
  try {
    const { code } = req.body;
    const { tokens } = await oauth2client.getToken(code);

    // Use the token to get the user's email
    oauth2client.setCredentials(tokens);
    const oauth2 = google.oauth2({ version: 'v2', auth: oauth2client });
    const { data } = await oauth2.userinfo.get();
    const email = data.email;

    // Save the token in MongoDB
    const user = await User.findOneAndUpdate(
      { email: email }, // Find the user by email
      {
        email: email,
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
        scope: tokens.scope,
        tokenType: tokens.token_type,
        expiryDate: tokens.expiry_date,
      },
      { upsert: true, new: true } // Create the user if not found, and return the updated document
    );

    // Redirect to browse.html
    res.status(200).send({ redirectUrl: 'http://127.0.0.1:5000/browse.html', message: 'Token stored successfully', user });
  } catch (error) {
    next(error);
  }
});

router.post('/create-event', async (req, res, next) => {
  try {
  const{title,location,description,startDateTime,endDateTime}=req.body
    oauth2client.setCredentials({refresh_token:token.refresh_token})
    const calendar=google.calendar("v3")
    const reponse=await calendar.events.insert({
      auth:oauth2client,
      requestBody:{
        title:title,
        description:description,
        location:location,
        colorId:6,
        start:{
          dateTime:new Date(startDateTime),
        },
        end:{
          dateTime:new Date(endDateTime)
        },
      },
    })
    res.send(response)
  } catch (error) {
    next(error);
  }
});

module.exports = router;
