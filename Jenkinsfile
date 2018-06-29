pipeline {
    agent any

    stages {
        stage("Unit-tests in Docker") {
            agent {
                dockerfile {
                    filename 'Dockerfile.testenv'
                }
            }

            steps {
                sh "tox -c tox.ini"
                junit "result.xml"
            }
        }

        stage("Docker build") {
            steps {
                sh "docker build -t docker2.molflow.com/odin_redo/odincal:${env.BUILD_TAG} ."
            }
        }

        stage("Docker push") {
            when { environment name: 'GITREF', value: 'master' }
            steps {
                sh """docker tag docker2.molflow.com/odin_redo/odincal:${env.BUILD_TAG} \\
                    docker2.molflow.com/odin_redo/odincal:latest
                """
                sh "docker push docker2.molflow.com/odin_redo/odincal"
            }
        }
    }

    post {
        success {
            sendmessage(PHID, "pass")
        }

        failure {
            sendmessage(PHID, "fail")
        }
    }
}


def sendmessage(phid, type) {
    withCredentials([string(credentialsId: 'conduit-token', variable: 'APITOKEN')]) {
        sh """curl https://phabricator.molflow.com/api/harbormaster.sendmessage \\
            -d api.token=$APITOKEN \\
            -d buildTargetPHID=$phid \\
            -d type=$type
        """
        sh """curl https://phabricator.molflow.com/api/harbormaster.createartifact \\
            -d api.token=$APITOKEN \\
            -d buildTargetPHID=$phid \\
            -d artifactKey=Jenkins \\
            -d artifactType=uri \\
            -d artifactData[name]='Jenkins build' \\
            -d artifactData[uri]=$BUILD_URL \\
            -d artifactData[ui.external]=true
        """
    }
}
