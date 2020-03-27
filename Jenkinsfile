node() {
    def odincalImage
    stage('build') {
        checkout scm
        odincalImage = docker.build("docker2.molflow.com/odin_redo/odincal:${env.BUILD_TAG}")
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
    if (env.GITREF == 'master') {
        stage('push') {
            odincalImage.push()
            odincalImage.push('latest')
        }
    }
}
