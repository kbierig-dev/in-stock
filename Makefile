# Makefile for generating AWS Lambda deployment package

# Variables
SCRIPT_NAME = add_to_cart.py
LAMBDA_FUNC = lambda_function.py
ZIP_NAME = in_stock_lambda.zip

include .env
export $(shell sed 's/=.*//' .env)

.PHONY: all package clean

all: package

package:
	@echo "Packaging $(SCRIPT_NAME) for AWS Lambda..."
	@cp $(SCRIPT_NAME) $(LAMBDA_FUNC)
	@zip $(ZIP_NAME) $(LAMBDA_FUNC)
	@echo "Successfully created $(ZIP_NAME)"

clean:
	@echo "Cleaning up generated files..."
	@rm -f $(LAMBDA_FUNC) $(ZIP_NAME)
	@echo "Clean complete."
