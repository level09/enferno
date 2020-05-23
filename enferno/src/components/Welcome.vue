<template>
    <div class="main" style="text-align: center; padding:40px;">

        <a href="/"><img :src="logo" alt="enferno"></a>

        <h3>Welcome!</h3>

        <p>Congratulations! Enferno framework has been installed successfully. </p>


        <p>
            <a href="/register">Sign up</a> or <a href="/login">Sign in</a>
        </p>


    </div>
</template>

<script>
    export default {
    props : ['logo']
    }
</script>