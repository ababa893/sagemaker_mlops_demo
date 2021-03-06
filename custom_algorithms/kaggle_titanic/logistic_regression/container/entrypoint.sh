#!/bin/bash

# [本スクリプトについて]
# ローカルAPIテスト環境構築に使用
# build_and_push.shによって，SageMakerAPI用コンテナイメージ作成の際に本スクリプトをコンテナ内の/opt/programにコピー
# `$ docker run -it -d -v -p 8080:8080 -e {環境変数設定} ... {作成したイメージ} entrypoint.sh`
# サーバが立ち上がったあとに，
# http://localhost:8080 宛にリクエストを投げるテストコードtest_predictor.py 実行を想定

# AWS CLI 用の環境変数を設定（docker run 時に，--envオプションで必要な環境変数が渡されていることを想定）
# （CircleCI上でdocker run する場合は，予め管理画面にてAWS CLI 用環境変数をcontextまたはEnvironment Variablesに設定しておくこと．）
echo "Create AWS CLI setting files"
mkdir ~/.aws 
echo -e "[default]\naws_access_key_id=$AWS_ACCESS_KEY_ID_DEV\naws_secret_access_key=$AWS_SECRET_ACCESS_KEY_DEV\n" > ~/.aws/credentials
echo -e "[stg]\naws_access_key_id=$AWS_ACCESS_KEY_ID_STG\naws_secret_access_key=$AWS_SECRET_ACCESS_KEY_STG\n" >> ~/.aws/credentials
echo -e "[prd]\naws_access_key_id=$AWS_ACCESS_KEY_ID_PRD\naws_secret_access_key=$AWS_SECRET_ACCESS_KEY_PRD\n" >> ~/.aws/credentials
echo -e "[default]\nregion=$REGION\n[stg]\nregion=$REGION\n[prd]\nregion=$REGION\n" > ~/.aws/config

echo "Prepare API local server"
# trainスクリプトでS3から/opt/ml/modelディレクトリに推論用ファイルをDL
train
# serveスクリプトでサーバ立ち上げ Listen状態にする
serve