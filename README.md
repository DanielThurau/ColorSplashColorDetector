# ColorSplashColorDetector

## Description

(CSCD) is a component of the overarching ColorSplash web application that can be found at https://thurau.io/colorsplash/. ColorSplash allows users to browse royalty free images that have colors within a certain Euclidean distance of a provided HEX code. CSCD runs in a python-3.8 AWS Lambda runtime and uses [scipy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.KDTree.html#scipy.spatial.KDTree) to load processed image data into a *[k-d tree](https://en.wikipedia.org/wiki/K-d_tree)*. CSCD is invoked via API Gateway via HTTP GET requests and returns a JSON object with URLS to unsplash images.

You can see other components of this project in the following Github repos:

- [ColorSplashPhotoRetrieval](https://github.com/DanielThurau/ColorSplashPhotoRetrieval)
- [ColorSplashColorDetector](https://github.com/DanielThurau/ColorSplashColorDetector)
- [thurau.io](https://github.com/DanielThurau/thurau.io)
- [colorsplash-common](https://github.com/DanielThurau/colorsplash-common)

## Motivation

A friend was facing issues when trying to create social media posts for an ecommerce company we recently launched. She had developed a branding guide and had chosen what colors she wanted to include in the website, logos, and eventual marketing material. But when it was time to make marketing posts, trying to apply that style guide was difficult. For all the tools on the internet she used, none were able to query royalty free images that were close to the HEX color codes she had selected. This project was born to remedy this issue. 

I wanted to provide a clean minimal interface on a website that would have a form for a HEX code, and query a REST API that would return royalty free images that had a subset of colors within close to the original HEX code.


## Features And Roadmap

### Features
1. Lambda triggered via API Gateway GET Requests
2. Uses *k-d trees* to ball point a set of n-dimensional coordinates close to a given n-dimensional point
3. AWS Infrastructure defined in template.yml
4. Machine-specific libraries deployed using Lambda Layers

### Roadmap
1. Write unit tests
2. Define the rest of the infrastructure used in the template.yml
3. CI/CD so `$ sam deploy` is triggered from Github
4. Have distance also be a query parameter
5. Scanning pagination for larger datasets
6. More DB effcient lookups by limiting the number of urls to be queried to max_content_length

## Tech Used

Due to CSCD's request/response nature, I knew I had to integrate with some sort of API provider. Due to my history with AWS, I decided to use AWS as the cloud provider and write the project as a aPI Gateway + serverless application that is deployed using the AWS Serverless Application Model (AWS SAM) CLI tool. You can find out more about AWS SAM on its [homepage](https://aws.amazon.com/serverless/sam/).


CSCD's role is to serve user requests to the web application. It has a publicly accessible API that the React App sends GET requests from with the user's desired HEX code. The API will trigger a lambda with the event where the backend logic to find already processed RGB coordinates that are within a Eucledian distance of the provided HEX code executes. CSCD will scan the RGB table and produce all of the RGB coordinates that have been processed. These coordinates will be loaded into scipy's kdtree data structured and ball point queried with a provided distance. The top closest results will then be looked up in a database and return urls to images that have those RGB coordinates in them.

A longer writeup on this can be found here (//TODO include the blogpost here).

## Installation

### Required Tools
1. [git](https://git-scm.com/) - a free and open source distributed version control system
2. [python 3.8](https://www.python.org/downloads/release/python-380/) - an interpreted high-level general-purpose programming language. Includes pip a python dependency management tool
3. [Docker](https://www.docker.com/get-started) - an open source containerization platform. Required to run AWS SAM
4. [AWS CLI](https://aws.amazon.com/cli/) - a unified tool to manage your AWS services
5. [AWS SAM CLI](https://aws.amazon.com/serverless/sam/) - an open-source framework for building serverless applications

### Cloning The Project

You can either fork the repo or clone it directly with

```shell
$ git clone https://github.com/DanielThurau/ColorSplashColorDetector.git
$ cd ColorSplashColorDetector
```

### Configuring AWS

AWS SAM CLI will piggy back off of the AWS CLI configurations. It is worth while to configure this ahead of time. If considering contribution, open an issue on the project and credentials **may** be provided. If you want to clone and deploy to your own AWS accounts, configure your AWS CLI to have credentials via the `~/.aws/credentials` file. It will look like this

```shell
$ aws configure
AWS Access Key ID [None]: <your access key>
AWS Secret Access Key [None]: <your secret key>
Default region name [None]: <deployed region>
Default output format [None]: json
```

### Environmental Variables

There are several environmental variables needed to run this application. An example structure is found in `env.example` (// TODO Link this). Once you fill out the variables for local development, copy it to the src/ folder. The Lambda will also need to be configured with these values in the "Configuration-> Environmental Variables" via the AWS Console.

```shell
$ cp env.example src/.env
```

### AWS Infrastructure

This project uses AWS Lambda, AWS DynamoDB, AWS S3, and AWS CloudWatch. Since it's an AWS SAM application, the infrastructure is defined via the template.yml file which SAM will compile and create a CloudFormation stack. Most of the infrastructure for this component is written in this template.yml, but not all. See the **Roadmap** section to track upcoming improvements. If forking and deploying to a personal AWS account, some of the infrastructure will be missing and need to be manually created.

## Usage

This project uses AWS SAM CLI to build, test, and deploy, but running the code and unit tests via the python executable is also possible. However, it is advisable to use SAM CLI since the tool will mimic the lambda runtime.

### AWS SAM CLI

Start docker either as a background process, in another terminal tab, or via desktop application.

```shell
$ sam build
$ sam local invoke ColorSplashPhotoDetectorFunction --event events/event.json
$ sam local start-api
$ curl http://localhost:3000/
$ sam deploy
```

### Python

```shell
$ pip install -r tests/requirements.txt --user
$ python -m pytest tests/unit -v
$ AWS_SAM_STACK_NAME=ColorSplashColorDetector python -m pytest tests/integration -v
```

It is worthwhile to have some form of virtualenv while developing on this pacakge for both the IDE and development. I recommend [conda](https://docs.conda.io/en/latest/).

## Contribute

If you'd like to contribute, fork the project and submit a Pull Request. If you'd like access to the infrastructure to test, open an issue and request access. Access requests will be reviewed and granted on a case by case basis.

## Credits

So many tutorials and blog posts deserve to have credits here, but alas I did not think to record all of them. I will be trying to fill this in as I write the ColorSplash blog post. Here are a few that are specific to this component.

* [Color Identification in Images](https://towardsdatascience.com/color-identification-in-images-machine-learning-application-b26e770c4c71) - [Karan Bhanot](https://medium.com/@bhanotkaran22)

    * This tutorial provided some of the code examples and explaination on how to accomplish the color detection and grouping
* [Marcin's](https://stackoverflow.com/users/248823/marcin) answer on [StackOverflow](https://stackoverflow.com/a/64019186/6655640)

    * To get some of these libraries to work in the lambda runtime required a special feature of AWS Lambdas called Lambda Layers. To have gotten this component working in the asynchronous context wouldn't have been possible without his contribution.

## License

See LICENSE.md

> MIT License
>
> Copyright (c) 2021 Daniel Thurau
