
const ChatBox = {
  data() {
    return {
      session_uuid: null,
      user_uuid: null,
      payload: null,
      utterances: [
          {speaker: 'bot', 'text': 'Hi this is Chirpy! What\'s your name?'},
          {speaker: 'user', 'text': "I'm ashwin. How are you doing?"},
          {speaker: 'bot', 'text': "I'm fine. What did you do today?"},
          {speaker: 'user', 'text': "I went out for a game of basketball"},
      ],
      newUtterance: '',
    }
  },
  methods: {
    pushUtterance: function(speaker, text) {
      this.utterances.push({speaker: speaker, text: text});
      this.$nextTick(function(){
          var element = document.getElementsByClassName("transcript");
          element[0].scrollTop = element[0].scrollHeight;
      });
    },
    submit: function(){
      var that = this;
      this.pushUtterance('user', this.newUtterance);
      axios.post('http://localhost:5001/conversation', {
        payload: this.payload,
        session_uuid: this.session_uuid,
        user_uuid: this.user_uuid,
        user_utterance: this.newUtterance
      })
          .then(function(response) {
            var data = response.data;
            that.pushUtterance('bot', data.bot_utterance);
            that.payload = data.payload;
            that.session_uuid= data.session_uuid;
            that.user_uuid = data.user_uuid;
            console.log(response);
          })
          .catch(function(error){
            console.log(error);
          });
      this.newUtterance= '';
    }

  }
}
const app = Vue.createApp(ChatBox);
const vm = app.mount("#app")