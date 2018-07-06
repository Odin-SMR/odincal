@Library('molflow') _

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
                sh "docker push docker2.molflow.com/odin_redo/odincal:latest"
            }
        }
    }

    post {
        always {
          setPhabricatorBuildStatus PHID
        }
    }
}
