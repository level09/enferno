var gulp = require('gulp'),
    minifyCSS = require('gulp-minify-css'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify');

gulp.task('css',function(){
    return gulp.src('static/css/*.css')
        .pipe(concat('app.css'))
        .pipe(minifyCSS())
        .pipe(gulp.dest('static/build/css'))
});

gulp.task('js',function(){
    //define scripts as array so we can prioritize them
    return gulp.src([
        'static/js/main.js'
            ]
    )
        .pipe(concat('app.js'))
        .pipe(uglify())
        .pipe(gulp.dest('static/build/js'))
})


gulp.task('default',function(){

    gulp.watch('static/css/*.css',['css']);
    gulp.watch('static/js/*.js',['js']);

})