pipeline {
    agent any

    stages {
        
        stage("Clone Git Repository") {
            steps {
                git(
                    url: "https://github.com/boneyd7511/ntca",
                    branch: "master",
                    changelog: true,
                    poll: true
                )
            }
        }

        stage("Create Report File") {
            steps {
                script {
                    def time = sh(script: 'date "+%F-%T"', returnStdout: true).trim()
                    env.REPORT = "jenkins-reports/python_report_${time}.txt"
                    sh "touch ${env.REPORT}"
                }
            }
        }

        stage('Format') {
            steps {
                echo 'Formatting..'
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    sh "echo '__________FORMATTING REPORT__________' >> ${env.REPORT}"
                    sh "ruff format >> ${env.REPORT}"
                }
                sh "echo '\n' >> ${env.REPORT}"
            }
        }
        
        stage('Lint') {
            steps {
                echo 'Linting..'
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    sh "echo '__________LINTING REPORT__________' >> ${env.REPORT}"
                    sh "find . -name '*.py' -exec pylint {} + >> ${env.REPORT}"
                }
                sh "echo '\n' >> ${env.REPORT}"
            }
        }
        
        stage('Security Scanner') {
            steps {
                echo 'Beginning Security Scan..'
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    sh "echo '__________SECURITY SCANNER REPORT__________' >> ${env.REPORT}"
                    sh "bandit -r . >> ${env.REPORT}"
                }
                sh "echo '\n' >> ${env.REPORT}"
            }
        }
        
        stage('Git Push') {
            steps {
                echo 'Trying push to GitHub...'
                catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
                    withCredentials([gitUsernamePassword(credentialsId: 'boneyd7511-github-token', gitToolName: 'Default')]) {
                        sh 'git add .'
                        sh 'git commit -m "Push from Jenkins Python Pipeline"'
                        sh 'git push -u origin master'
                    }
                }
            }
        }
    }
}
