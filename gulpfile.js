var gulp = require('gulp'),
    minifyCSS = require('gulp-minify-css'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify');

gulp.task('css',function(){
    return gulp.src('static/_css/*.css')
        .pipe(concat('app.css'))
        .pipe(minifyCSS())
        .pipe(gulp.dest('static/css'))
});

gulp.task('js',function(){
    //define scripts as array so we can prioritize them
    return gulp.src([
        'static/_js/main.js'
            ]
    )
        .pipe(concat('app.js'))
        .pipe(uglify())
        .pipe(gulp.dest('static/js'))
})


gulp.task('default',function(){
    gulp.start('css','js');
    gulp.watch('gulpfile.js');
    gulp.watch('static/_css/*.css',['css']);
    gulp.watch('static/_js/*.js',['js']);

})