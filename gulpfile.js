var gulp = require('gulp'),
    minifyCSS = require('gulp-minify-css'),
    compass = require('gulp-compass'),
    concat = require('gulp-concat'),
    uglify = require('gulp-uglify');

gulp.task('css',function(){
    return gulp.src('enferno/static/_css/*.css')
        .pipe(concat('style.css'))
        .pipe(minifyCSS())
        .pipe(gulp.dest('enferno/static/css'))
});

gulp.task('js',function(){
    //define scripts as array so we can prioritize them
    return gulp.src([
        'enferno/static/_js/main.js'
            ]
    )
        .pipe(concat('app.js'))
        .pipe(uglify())
        .pipe(gulp.dest('enferno/static/js'))
});

gulp.task('compass', function() {
  gulp.src('./enferno/static/scss/*.scss')
    .pipe(compass({
      css: './enferno/static/css',
      sass: './enferno/static/scss',
      //uncomment if you would like to include susy grids
      //require: ['susy']
    }))
    .pipe(gulp.dest('enferno/static/css'));
});



gulp.task('default',function(){
    gulp.start('compass','css','js');
    gulp.watch('gulpfile.js');
    gulp.watch('enferno/static/_css/*.css',['css']);
    gulp.watch('enferno/static/_js/*.js',['js']);
    gulp.watch('enferno/static/scss/*.scss',['compass']);

})