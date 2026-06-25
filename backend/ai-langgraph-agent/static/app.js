let recognition;

function speak(text){

const avatar =
document.getElementById("avatar");

avatar.classList.add("talking");

let utterance =
new SpeechSynthesisUtterance(text);

utterance.rate = 1;

speechSynthesis.speak(
utterance
);

utterance.onend = ()=>{

avatar.classList.remove(
"talking"
);

};

}

function addBot(text){

let chat =
document.getElementById(
"chat-box"
);

let div =
document.createElement("div");

div.className = "bot";

chat.appendChild(div);

let i = 0;

let interval =
setInterval(()=>{

div.innerHTML += text[i];

i++;

if(i >= text.length){

clearInterval(interval);

speak(text);

}

},15);

}

function addUser(text){

let chat =
document.getElementById(
"chat-box"
);

chat.innerHTML +=
`<div class="user">${text}</div>`;

document
.getElementById(
"transcript"
)
.innerHTML +=
`<p>${text}</p>`;
}

async function startInterview(){

const username =
document.getElementById(
"username"
).value;

const token =
document.getElementById(
"token"
).value;

document
.getElementById(
"profile-section"
)
.innerHTML =
`

<div class="profile-card">
<img src="https://github.com/${username}.png">
<div>
<h2>${username}</h2>
<p>Analyzing GitHub...</p>
</div>
</div>
`;

let progress =
0;

let timer =
setInterval(()=>{

progress += 10;

document
.getElementById(
"progress-bar"
)
.style.width =
progress+"%";

},300);

const response =
await fetch("/start",{

method:"POST",

headers:{
"Content-Type":
"application/json"
},

body:JSON.stringify({

github_username:
username,

github_token:
token

})

});

clearInterval(timer);

document
.getElementById(
"progress-bar"
)
.style.width="100%";

const data =
await response.json();

document
.getElementById(
"repo-grid"
)
.innerHTML =
data.repo_cards;

addBot(
data.question
);

}

function startListening(){

recognition =
new webkitSpeechRecognition();

recognition.lang =
"en-US";

recognition.interimResults =
true;

recognition.start();

recognition.onresult =
async function(event){

let transcript = "";

for(
let i=0;
i<event.results.length;
i++
){

transcript +=
event.results[i][0]
.transcript;

}

document
.getElementById(
"avatar-status"
)
.innerHTML =
"Listening...";

if(
event.results[
event.results.length-1
].isFinal
){

addUser(
transcript
);

const response =
await fetch(
"/answer",
{
method:"POST",
headers:{
"Content-Type":
"application/json"
},
body:JSON.stringify({
answer:transcript
})
}
);

const data =
await response.json();

addBot(
data.question
);

}

};

}
