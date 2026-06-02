FICHIERS À PLACER ICI (générés par le pipeline Python)
======================================================

1. model.tflite   <- produit par : python model/export_tflite.py
2. vocab.txt       <- produit par : python model/train.py (sauvegarde du tokenizer)

Copiez ces deux fichiers depuis model/artifacts/ vers ce dossier
(android-app/app/src/main/assets/) avant de compiler l'application.

Sans ces fichiers, l'app compile et démarre quand même : le classifieur texte
renvoie une probabilité neutre (0.5) et seul le signal d'URL pilote le verdict.
Une fois model.tflite présent, l'inférence DistilBERT s'active automatiquement.
