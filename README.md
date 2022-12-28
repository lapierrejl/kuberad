## Building 
`docker build -t kuberad .`

## Usage

To run using your current set kube context:
`docker run -it -v ~/.kube:/root/.kube -v ~/.aws:/root/.aws/ kuberad`

To run on a specific kube context
`docker run -it -v ~/.kube:/root/.kube -v ~/.aws:/root/.aws/ kuberad --context=<context-name>`

To run on all kube contexts
`docker run -it -v ~/.kube:/root/.kube -v ~/.aws:/root/.aws/ kuberad --allcontexts`

To run on all contexts in which the context name contains a specific substring
`docker run -it -v ~/.kube:/root/.kube -v ~/.aws:/root/.aws/ kuberad --allcontexts --contains=bolt`