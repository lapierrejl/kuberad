from multiprocessing.dummy import Pool

import click
from jinja2 import Template

import libs.apiclients as apiclients

THREADPOOL_SIZE = 10

TEMPLATE = """
#### {{context}}
{% for removed_api in removed_apis -%}
- name: {{removed_api["name"]}}
  - type: {{removed_api["type"]}}
  - labels: {{removed_api["labels"]}}
  - removed_references: {{removed_api["removed_api_references"]}}
  - required_api: {{removed_api["required_api"]}}
  - managed_fields:
    {% for managed_field in removed_api["managed_fields"] -%}
    - manager: {{managed_field["manager"]}}
        api_version: {{managed_field["api_version"]}}
        time: {{managed_field["time"]}}
    {% endfor %}       
{% endfor %}
"""


def runner(context: str):
    
    removed_apis = []
    admission = apiclients.Admission(
        removed_apis=['admissionregistration.k8s.io/v1beta1'],
        required_api= 'admissionregistration.k8s.io/v1',
        context=context 
    )

    apiextension = apiclients.Apiextension(
        removed_apis=['apiextensions.k8s.io/v1beta1'],
        required_api='apiextensions.k8s.io/v1',
        context=context 
    )

    apiregistraion = apiclients.Apiregistration(
        removed_apis=['apiregistration.k8s.io/v1beta1'],
        required_api='apiregistration.k8s.io/v1',
        context=context 
    )
    
    autoscaling = apiclients.Autoscaling(
        removed_apis=['autoscaling/v2beta1', 'autoscaling/v2beta2'],
        required_api='autoscaling/v2',
        context=context 
    )

    batch = apiclients.Batch(
        removed_apis=['batch/v1beta1'],
        required_api='batch/v1',
        context=context 
    )

    certificates = apiclients.Certificates(
        removed_apis=['certificates.k8s.io/v1beta1'],
        required_api='certificates.k8s.io/v1',
        context=context 
    )

    coordination = apiclients.Coordination(
        removed_apis=['coordination.k8s.io/v1beta1'],
        required_api='coordination.k8s.io/v1',
        context=context 
        )
    
    discovery = apiclients.Discovery(
        removed_apis=['discovery.k8s.io/v1beta1'],
        required_api='discovery.k8s.io/v1',
        context=context 
    )

    events = apiclients.Events(
        removed_apis=['events.k8s.io/v1beta1'],
        required_api='events.k8s.io/v1',
        context=context 
    )
    
    networking = apiclients.Networking(
        removed_apis=['extensions/v1beta1', 'networking.k8s.io/v1beta1'],
        required_api='networking.k8s.io/v1', 
        context=context 
    )

    node = apiclients.Node(
        removed_apis=['node.k8s.io/v1beta1'],
        required_api='node.k8s.io/v1',
        context=context 
    )

    policy = apiclients.Policy(
        removed_apis=['policy/v1beta1'],
        required_api='policy/v1',
        context=context 
    )
    
    policyv1beta1 = apiclients.PolicyV1beta1(
        removed_apis=['policy/v1beta1'],
        required_api='',
        context=context,
        excluded_manifest_names=['eks.privileged']
    )

    rbac = apiclients.RBAC(
        removed_apis=['rbac.authorization.k8s.io/v1beta1'],
        required_api='rbac.authorization.k8s.io/v1',
        context=context 
    )

    scheduling = apiclients.Scheduling(
        removed_apis=['scheduling.k8s.io/v1beta1'],
        required_api='scheduling.k8s.io/v1',    
        context=context 
        )

    storage = apiclients.Storage(
        removed_apis=['storage.k8s.io/v1beta1'],
        required_api='storage.k8s.io/v1',
        context=context 
    )

    removed_apis.extend(autoscaling.find_removed_apis_hpa())
    removed_apis.extend(batch.find_removed_apis_cronjobs())
    removed_apis.extend(events.find_removed_apis_event())
    removed_apis.extend(discovery.find_removed_apis_enpoint_slices())
    removed_apis.extend(policy.find_removed_apis_pdb())
    removed_apis.extend(node.find_removed_apis_runtime_class())
    # removed_apis.extend(coordination.find_removed_apis_leases())
    # removed_apis.extend(admission.find_removed_apis_mutatating_web_hooks())
    # removed_apis.extend(admission.find_removed_apis_validating_web_hooks())
    # removed_apis.extend(apiextension.find_removed_apis_crds())
    # removed_apis.extend(apiregistraion.find_removed_apis_apiservices())
    # removed_apis.extend(certificates.find_removed_apis_csr())
    # removed_apis.extend(certificates.find_removed_apis_csr())
    # removed_apis.extend(networking.find_removed_apis_ingress_classes())
    # removed_apis.extend(networking.find_removed_apis_ingresses())
    # removed_apis.extend(rbac.find_removed_apis_cluster_role())
    # removed_apis.extend(rbac.find_removed_apis_cluster_role_bindings())
    # removed_apis.extend(rbac.find_removed_apis_role())
    # removed_apis.extend(rbac.find_removed_apis_rolebinding())
    # removed_apis.extend(scheduling.find_removed_apis_priority_classes())
    # removed_apis.extend(storage.find_removed_apis_csi_drivers())
    # removed_apis.extend(storage.find_removed_apis_csi_nodes())
    # removed_apis.extend(storage.find_removed_apis_storage_classes())
    # removed_apis.extend(storage.find_removed_apis_volume_attachments())
    removed_apis.extend(policyv1beta1.find_removed_apis_pod_security_policy())
    if removed_apis:
        report = Template(TEMPLATE)
        print(report.render(removed_apis=removed_apis, context=context))   

@click.command()
@click.option('--context', default="", help='Kubernetes context.')
@click.option('--allcontexts', is_flag=True)
@click.option('--contains', default="", help='Substring to match in context name')
def main(context, allcontexts, contains):
    if context:
        contexts = [context]
    elif allcontexts:
        contexts = [ x for x in apiclients.get_kube_contexts() if contains in x ]
    else:
        contexts = apiclients.get_kube_contexts(current=True)
    pool = Pool(THREADPOOL_SIZE)
    pool.map(runner, contexts)
    pool.close()
    pool.join()
    
if __name__ == "__main__":
    main()