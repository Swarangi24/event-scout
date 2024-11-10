import './App.css';
import {GoogleLogin} from 'react-google-login'
import axios from 'axios'
import {useState} from "react";
function App() {

const responseGoogle = (response) => {
  console.log(response);
  const { code } = response;
  axios.post('/api/create-token', { code })
    .then((response) => {
      console.log(response.data);
      if (response.data.redirectUrl) {
        // Redirect to browse.html
        window.location.assign(response.data.redirectUrl);
      }
    })
    .catch((error) => {
      console.log(error.message);
    });
};


    const responseError=error=>{
        console.log(error)
    }

    const handleSubmit=(e)=>{
        e.preventDefault()
        axios.post('/api/create-event',{
            title,location,description,startDateTime,endDateTime,timeZone,
        }).then(response=>{
                console.log(response.data)
            })
            .catch(error=>{console.log(error.message)})
    }


    const [title, setTitle] = useState('');
    const [location, setLocation] = useState('');
    const [description, setDescription] = useState('');
    const [startDateTime, setStartDateTime] = useState('');
    const [endDateTime, setEndDateTime] = useState('');
    const [timeZone, setTimeZone] = useState('UTC');

    return (
        <div>
            <div className="App">
                <h1>Google Calendar API</h1>
            </div>
            <div>
          <GoogleLogin
              clientId='912370917797-c08nfe40bnvl9qog13uml20n2gieqhea.apps.googleusercontent.com'
          buttonText='Sign in & Authorize Calendar'
          onSuccess={responseGoogle}
          onFailure={responseError}
          cookiePolicy={'single_host_origin'}
          responseType='code'
          accessType='offline'
          scope='openid email profile https://www.googleapis.com/auth/calendar'/>
            </div>
        </div>
    );
}

export default App;


