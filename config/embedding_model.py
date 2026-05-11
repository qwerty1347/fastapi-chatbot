class EmbeddingModel:
    MODELS = {
        'hugging_face': {
            'sentence_transformer': {
                'All-MiniLM-L6-v2': {
                    'name': 'all-MiniLM-L6-v2',
                    'size': 384,
                    'distance': 'Cosine'
                }
            }
        }
    }