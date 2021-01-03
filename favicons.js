var favicons = require('favicons'),
    path = require('path'),
    fs = require("fs"),
    source = './enferno/src/favicons/enferno.svg',                     // Source image(s). `string`, `buffer` or array of `string`
    configuration = {
        path: "/static/dist/favicons/",                                // Path for overriding default icons path. `string`
        appName: 'Enferno',                            // Your application's name. `string`
        appShortName: 'Enfenro',                       // Your application's short_name. `string`. Optional. If not set, appName will be used
        appDescription: 'Enferno Framework',                     // Your application's description. `string`
        developerName: 'Nidal Alhariri',                      // Your (or your developer's) name. `string`
        developerURL: 'https://enferno.io',                       // Your (or your developer's) URL. `string`
        dir: "auto",                              // Primary text direction for name, short_name, and description
        lang: "en-US",                            // Primary language for name and short_name
        background: "#fff",                       // Background colour for flattened icons. `string`
        theme_color: "#fff",                      // Theme color user for example in Android's task switcher. `string`
        appleStatusBarStyle: "black-translucent", // Style for Apple status bar: "black-translucent", "default", "black". `string`
        display: "standalone",                    // Preferred display mode: "fullscreen", "standalone", "minimal-ui" or "browser". `string`
        orientation: "any",                       // Default orientation: "any", "natural", "portrait" or "landscape". `string`
        scope: "/",                               // set of URLs that the browser considers within your app
        start_url: "/?homescreen=1",              // Start URL when launching the application from a device. `string`
        version: "1.0",                           // Your application's version string. `string`
        logging: false,                           // Print logs to console? `boolean`
        pixel_art: false,                         // Keeps pixels "sharp" when scaling up, for pixel art.  Only supported in offline mode.
        loadManifestWithCredentials: false,       // Browsers don't send cookies when fetching a manifest, enable this to fix that. `boolean`
        icons: {
            android: true,              // Create Android homescreen icon. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            appleIcon: true,            // Create Apple touch icons. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            appleStartup: false,         // Create Apple startup images. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            coast: false,                // Create Opera Coast icon. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            favicons: true,             // Create regular favicons. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            firefox: true,              // Create Firefox OS icons. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            windows: true,              // Create Windows 8 tile icons. `boolean` or `{ offset, background, mask, overlayGlow, overlayShadow }`
            yandex: false
        }
    },
    callback = function (error, response) {
        if (error) {
            console.log(error.message); // Error description e.g. "An unknown error has occurred"
            return;
        }
        //console.log(response.images);   // Array of { name: string, contents: <buffer> }
        //console.log(response.files);    // Array of { name: string, contents: <string> }
        //console.log(response.html);     // Array of strings (html elements)
        var target = './enferno/static/dist/favicons/';
        if (!fs.existsSync(target)) {
            fs.mkdirSync(target);

        }

        for (file of response.files) {
            fs.writeFile(path.resolve(target + file.name), file.contents, function (err) {
                if (err) {
                    console.error(err);
                }

                return;
            });
        }
        for (image of response.images) {
            fs.writeFile(path.resolve(target + image.name), image.contents, function (err) {
                if (err) {
                    console.error(err);
                }

                return;
            });
        }
        console.log('Succesfully generated favicons to enferno/static/dist/favicons/');


    };


favicons(source, configuration, callback);
