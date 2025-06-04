# Bookit
Each person working on a new feature creates a new branch named in the format: person name-feature name. They only push their changes to this branch. Once approved by the other team members, the branch is merged with the develop branch. After performing comprehensive tests, if everything is verified, the branch is merged into the master branch.

If issues arise during testing, a new branch named fix-bug is created to address the problems. After the fixes are approved and verified, the branch is first merged into develop and then into master.

In case bugs occur in the master branch, a hotfix branch is created. Once the hotfix is completed and tested on the develop branch, it is merged into master.
