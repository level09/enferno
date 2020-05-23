<template>

    <div id="app">
        <Welcome logo="/static/img/enferno.svg" />
    </div>


</template>

<script>
import 'modern-normalize/modern-normalize.css';
import Welcome from './components/Welcome'

    export default {
        name: 'app',

        data: () => ({

        }),
        components: {
            Welcome



        }
    }
</script>
