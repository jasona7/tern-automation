#!/bin/bash
amazon-linux-extras install docker
yum install -y git
systemctl start docker
cd /tmp
git clone https://github.com/tern-tools/tern.git
cd tern
echo "public.ecr.aws/bitnami/jenkins:2.303.3-debian-10-r16" >> manifest_test.txt
echo "public.ecr.aws/ubuntu/redis:5.0-20.04_edge" >> manifest_test.txt
echo "public.ecr.aws/ubuntu/ubuntu:22.04" >> manifest_test.txt
echo "public.ecr.aws/ubuntu/memcached:1.5-20.04_edge" >> manifest_test.txt
echo "public.ecr.aws/bitnami/ruby:2.7.4-debian-10-r136" >> manifest_test.txt
docker build -f docker/Dockerfile -t ternd .
containerfile="$PWD/manifest_test.txt"
while IFS= read -r line
do
  echo "$line"
  newformat=$(echo $line | sed -r 's/\//-/g; s/\:/-/g') 
  echo "REMOVE SPECIAL CHARS FOR OUTPUT FILE:" $newformat
  ./docker_run.sh ternd "report -i $line -y 1" > /tmp/$newformat.txt
  wait -f
  #echo $line | sed -r 's/\[:/}/-/g'
done < "$containerfile"
