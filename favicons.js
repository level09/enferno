import { favicons } from "favicons";
import path from 'path';
import fs from 'fs/promises';

const source = './enferno/src/favicons/enferno.svg';

const configuration = {
    path: "/static/favicons/",
    appName: 'Enferno',
    appShortName: 'Enferno',
    appDescription: 'Enferno Framework',
    developerName: 'Nidal Alhariri',
    developerURL: 'https://enferno.io',
    dir: "auto",
    lang: "en-US",
    background: "#fff",
    theme_color: "#fff",
    appleStatusBarStyle: "black-translucent",
    display: "standalone",
    orientation: "any",
    scope: "/",
    start_url: "/?homescreen=1",
    version: "1.0",
    pixel_art: false,
    loadManifestWithCredentials: false,
    icons: {
        android: true,
        appleIcon: true,
        appleStartup: false,
        favicons: true,
        windows: true,
        yandex: false,
    },
};

async function generateFavicons() {
    try {
        const response = await favicons(source, configuration);

        const target = './enferno/static/favicons/';
        await fs.mkdir(target, { recursive: true });

        for (const file of response.files) {
            await fs.writeFile(path.join(target, file.name), file.contents);
        }

        for (const image of response.images) {
            await fs.writeFile(path.join(target, image.name), image.contents);
        }

        console.log('Successfully generated favicons to enferno/static/favicons/');
    } catch (error) {
        console.error(error.message);
    }
}

generateFavicons();
