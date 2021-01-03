import "./index.css";
import Vue from "vue";
import Welcome from "./components/Welcome";


let app = new Vue({
    el: '#app',
    // workaround Jinja conflict with vue
    delimiters: ['${','}'],
    components : {
        Welcome
    }

})




