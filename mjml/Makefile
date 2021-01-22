
mjml-dev :
	npx cross-env NODE_ENV=development gulp -f gulpfile.mjml.js build

mjml-prod :
	npx cross-env NODE_ENV=production gulp -f gulpfile.mjml.js build

clean :
	npx cross-env gulp -f gulpfile.mjml.js clean

all : mjml-prod

.PHONY : mjml-dev mjml-prod clean
