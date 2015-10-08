var gulp = require('gulp'),
    minifyCSS = require('gulp-minify-css'),
    compass = require('gulp-compass'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify');

gulp.task('css',function(){
    return gulp.src('static/_css/*.css')
        .pipe(concat('style.css'))
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
});

gulp.task('compass', function() {
  gulp.src('./static/scss/*.scss')
    .pipe(compass({
      css: './static/css',
      sass: './static/scss',
      //uncomment if you would like to include susy grids
      //require: ['susy']
    }))
    .pipe(gulp.dest('static/css'));
});



gulp.task('default',function(){
    gulp.start('compass','css','js');
    gulp.watch('gulpfile.js');
    gulp.watch('static/_css/*.css',['css']);
    gulp.watch('static/_js/*.js',['js']);
    gulp.watch('static/scss/*.scss',['compass']);

})