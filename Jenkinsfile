node() {
    def odincalImage
    stage('build') {
        checkout scm
        odincalImage = docker.build("odinsmr/odincal:${env.BUILD_TAG}")
    }
    stage('test OOPS') {
        odincalImage.inside{
            sh "tox -c oops/tox.ini"
        }
    }
    stage('test odincal') {
        odincalImage.inside {
            sh "tox -c odincal/tox.ini"
        }
    }
    if (env.BRANCH_NAME == 'master') {
        stage('push') {
            withDockerRegistry([ credentialsId: "dockerhub-molflowbot", url: "" ]) {
                odincalImage.push()
                odincalImage.push('latest')
            }
        }
    }
}
