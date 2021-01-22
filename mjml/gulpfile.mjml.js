// Plugins
const gulp = require('gulp');
const nunjucks = require('gulp-nunjucks');
const mjml = require('gulp-mjml');
const rename = require('gulp-rename');
const path = require('path');
const del = require('del');
const pkg = require('./package.json');

// Select Development or Production Build
const devMode = process.env.NODE_ENV === 'development'

// Compile Nunjucks to MJML Templates
gulp.task('njk:compile', function() {
  return gulp.src('./templates/email/*.mjml.njk')
    .pipe(nunjucks.compile())
    .pipe(rename({ extname: '' })) /* remove .njk extension */
    .pipe(rename({ extname: '.mjml' }))
    .pipe(gulp.dest(path.resolve(__dirname)));
});

// Clean Nunjucks Templates
gulp.task('njk:clean', function() {
  return del([
    path.resolve(__dirname, '/*.mjml'),
  ])
});

// Build MJML Templates
gulp.task('mjml:build', function () {
  return gulp.src('./*.mjml')
    .pipe(mjml())
    .pipe(rename({ extname: '' })) /* remove .njk extension */
    .pipe(rename({ extname: '.html.j2' }))
    .pipe(gulp.dest(path.resolve(__dirname, '..', pkg.name, 'templates/email/html')));
});

// Clean MJML Templates
gulp.task('mjml:clean', function() {
  return del([
    path.resolve(__dirname, pkg.name, 'templates/email/html/*'),
  ])
});

// Build All
gulp.task('build', gulp.parallel(gulp.series('njk:compile', 'mjml:clean', 'mjml:build')));

// Clean All
gulp.task('clean', gulp.parallel('njk:clean', 'mjml:clean'));

// Default Task
gulp.task('default', gulp.series('build'));
