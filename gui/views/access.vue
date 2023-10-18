<script setup>
import { inject, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";
import { useAbilityStore } from "@/stores/abilityStore.js";
import { useAdversaryStore } from "@/stores/adversaryStore.js";
import { useAgentStore } from "@/stores/agentStore.js";

const abilityStore = useAbilityStore();
const { abilities } = storeToRefs(abilityStore);
const adversaryStore = useAdversaryStore();
const { adversaries } = storeToRefs(adversaryStore);
const agentStore = useAgentStore();
const { agents } = storeToRefs(agentStore);
const $api = inject("$api");

onMounted(async () => {
  await abilityStore.getAbilities($api);
  await adversaryStore.getAdversaries($api);
  await agentStore.getAgents($api);

});
const accessAbilities = computed(() =>
  abilities.value.filter((ability) => ability.plugin === "access")
);
const accessAdversaries = computed(() =>
  adversaries.value.filter((adversary) => adversary.plugin === "access")
);
const accessAgents = computed(() =>
  agents.value.filter((agent) => agent.plugin === "access")
);

</script>
<script>
    export default {
      data() {
        return {
          // Core variables
          agents: [],
          links: [],
          obfuscators: [],
          selectedObfuscator: 'base64',
          selectedAgent: {},
          selectedAgentPaw: '',
          abilities: [],
          filteredAbilities: [],
          selectedAbility: {},
          selectedAbilityId: '',
          tactics: [],
          selectedTactic: '',
          techniques: [],
          selectedTechnique: '',
          searchQuery: '',
          searchResults: [],
          // Modals
          showOutputModal: false,
          outputCommand: '',
          outputResult: '',
          showRunModal: false,
          facts: []
        };
      },
    
      mounted() {
        this.initPage();
      },
    
      methods: {
        async initPage() {
          try {
            this.agents = await apiV2('GET', '/api/v2/agents');
            this.abilities = await apiV2('GET', '/api/v2/abilities');
            this.obfuscators = await apiV2('GET', '/api/v2/obfuscators');
    
            while (this.$refs.headerAccess) {
              await this.sleep(3000);
              this.refreshAgents();
            }
          } catch (error) {
            this.toast('There was an error initializing the page', false);
            console.error(error);
          }
        },
    
        selectAgent() {
          this.selectedAgent = this.agents.find((agent) => agent.paw === this.selectedAgentPaw);
          this.links = this.selectedAgent.links;
          this.filterAbilitiesByPlatform();
        },
    
        filterAbilitiesByPlatform() {
          let platform = this.selectedAgent.platform;
          this.filteredAbilities = [];
          this.abilities.forEach((ability) => {
            let execPlatforms = ability.executors.map((exec) => exec.platform);
            if (execPlatforms.includes(platform)) {
              this.filteredAbilities.push(ability);
            }
          });
        },
    
        async refreshAgents() {
          try {
            this.agents = await apiV2('GET', '/api/v2/agents');
            if (this.selectedAgentPaw) {
              this.selectAgent();
            }
          } catch (error) {
            this.toast('There was an error refreshing the page', false);
            console.error(error);
          }
        },
    
        getLinkStatus(link) {
          if (link.status === 0) {
            return 'success';
          } else if (link.status > 0) {
            return 'failed';
          } else {
            return 'in progress';
          }
        },
    
        showOutput(link) {
          restRequest('POST', { 'index': 'result', 'link_id': link.unique }, (data) => {
            this.outputCommand = b64DecodeUnicode(link.command);
            try {
              this.outputResult = JSON.parse(b64DecodeUnicode(data.output));
            } catch (SyntaxError) {
              this.outputResult = ""
            }
            this.showOutputModal = true;
          });
        },
    
        searchForAbility() {
          this.searchResults = [];
          if (!this.searchQuery) return;
          this.filteredAbilities.forEach((ability) => {
            if (ability.name.toLowerCase().indexOf(this.searchQuery.toLowerCase()) > -1) {
              this.searchResults.push({
                ability_id: ability.ability_id,
                name: ability.name
              });
            }
          });
        },
    
        selectAbility(id) {
          this.searchQuery = [];
          this.searchResults = [];
          this.selectedAbility = this.abilities.find((ability) => ability.ability_id === id);
          this.selectedTactic = this.selectedAbility.tactic;
          this.selectedTechnique = this.selectedAbility.technique_id;
          this.selectedAbilityId = id;
          this.findFacts();
        },
    
        findFacts() {
          let rxp = /#{([^}]+)}/g;
          let match;
          let matches = [];
    
          let commands = this.selectedAbility.executors.map((exec) => exec.command);
          commands.forEach((command) => {
            while (match = rxp.exec(command)) {
              matches.push(match[1]);
            }
          });
          this.facts = [...new Set(matches)].map((fact) => { 
            return { trait: fact, value: '' };
          });
        },
    
        async execute() {
          if (this.facts.length && this.facts.filter((fact) => !fact.value).length) {
            this.toast('Fact values cannot be empty!', false);
            return;
          }
    
          let requestBody = {
            paw: this.selectedAgentPaw,
            ability_id: this.selectedAbilityId,
            facts: this.facts,
            obfuscator: this.selectedObfuscator
          };
    
          try {
            await apiV2('POST', '/plugin/access/exploit', requestBody);
            this.showRunModal = false;
            this.refreshAgents();
            this.toast('Executed ability', true);
          } catch (error) {
            console.error(error);
          }
        },
    
        sleep(ms) {
          return new Promise(resolve => setTimeout(resolve, ms));
        },
    
        toast(message, type) {
          // Your toast implementation here
        }
      }
    };
</script>

<template lang="pug">
.content
    h2 Access
    p Here you can task any agent with any ability from the database - outside the scope of an operation. This is especially useful for conducting initial access attacks. To do this, deploy an agent locally and task it with either pre-ATT&CK or initial access tactics, pointed at any target. You can even deploy an agent remotely and use it as a proxy to conduct your initial access attacks. To the right, you'll see every ability directly tasked to an agent.

// AGENT SELECTION

div
form
    #select-agent.field.has-addons
    label.label Select an agent
    .control.is-expanded
        .select.is-small.is-fullwidth
        select(x-on:change="selectAgent()" x-model="selectedAgentPaw")
            option(value="" disabled selected) Select an agent
            //- template(x-for="agent of agents", :key="agent.paw")
            //- option(x-bind:value="agent.paw" x-text="`${agent.host} - ${agent.paw}`")

//- div.has-text-centered.content(x-show="!selectedAgentPaw")
//- p Select an agent to get started

//- div(x-show="selectedAgentPaw")
//- .is-flex(x-show="selectedAgentPaw")
//-     button.button.is-primary.is-small.mr-4(@click="showRunModal = true")
//-     span.icon
//-         i.fas.fa-running
//-     span Run an Ability
//-     span.mr-4
//-     strong Agent Platform
//-     span(x-text="selectedAgent.platform")
//-     span
//-     strong Compatible Abilities
//-     span(x-text="filteredAbilities.length")
//- p.has-text-centered.content(x-show="!links.length") No links to show

//- div(x-show="selectedAgentPaw && links.length")
//- table.table.is-striped.is-fullwidth
//-     thead
//-     tr
//-         th order
//-         th name
//-         th tactic
//-         th status
//-         th
//-     tbody
//-     template(x-for="(link, index) of links", :key="link.unique")
//-         tr.pointer
//-         td(x-text="index + 1")
//-         td(x-text="link.ability.name")
//-         td(x-text="link.ability.tactic")
//-         td(x-text="getLinkStatus(link)" x-bind:class="{ 'has-text-danger': getLinkStatus(link) === 'failed', 'has-text-success': getLinkStatus(link) === 'success' }")
//-         td
//-             button.button.is-small.is-primary(@click="showOutput(link)") Output

//- // MODALS

//- div.modal(x-bind:class="{ 'is-active': showOutputModal }")
//- .modal-background(@click="showOutputModal = false")
//- .modal-card.wide
//-     header.modal-card-head
//-     p.modal-card-title Link Output
//-     section.modal-card-body
//-     label.label Command
//-     pre(x-text="outputCommand")
//-     label.label Standard Output
//-     pre(x-text="outputResult.stdout || '[ no output to show ]'")
//-     label.label Standard Error
//-     pre(x-text="outputResult.stderr || '[ no errors to show ]'")
//-     footer.modal-card-foot
//-     nav.level
//-         .level-left
//-         .level-right
//-         .level-item
//-             button.button.is-small(@click="showOutputModal = false") Close

//- div.modal(x-bind:class="{ 'is-active': showRunModal }")
//- .modal-background(@click="showRunModal = false")
//- .modal-card
//-     header.modal-card-head
//-     p.modal-card-title Run an Ability
//-     section.modal-card-body
//-     p.has-text-centered Select an Ability
//-     form
//-         .field.is-horizontal
//-         .field-label.is-small
//-             label.label
//-             span.icon.is-small
//-                 i.fas.fa-search
//-         .field-body
//-             .field
//-             .control
//-                 input.input.is-small(x-model="searchQuery" placeholder="Search for an ability..." x-on:keyup="searchForAbility()")
//-                 .search-results
//-                 template(x-for="result of searchResults", :key="result.ability_id")
//-                     p(@click="selectAbility(result.ability_id)" x-text="result.name")
//-     form
//-         .field.is-horizontal
//-         .field-label.is-small
//-             label.label Tactic
//-         .field-body
//-             .field
//-             .control
//-                 div.select.is-small.is-fullwidth
//-                 select(x-model="selectedTactic" x-on:change="selectedAbilityId = ''")
//-                     option(default) Choose a tactic
//-                     template(x-for="tactic of [...new Set(filteredAbilities.map((e) => e.tactic))]", :key="tactic")
//-                     option(x-bind:value="tactic" x-text="tactic")
//-         .field.is-horizontal
//-         .field-label.is-small
//-             label.label Technique
//-         .field-body
//-             .field
//-             .control
//-                 div.select.is-small.is-fullwidth
//-                 select(x-model="selectedTechnique" x-bind:disabled="!selectedTactic" x-on:change="selectedAbilityId = ''")
//-                     option(default) Choose a technique
//-                     template(:key="exploit.technique_id" x-for="exploit of [...new Set(filteredAbilities.filter((e) => selectedTactic === e.tactic).map((e) => e.technique_id))].map((t) => filteredAbilities.find((e) => e.technique_id === t))")
//-                     option(x-bind:value="exploit.technique_id" x-text="exploit.technique_id")
//-         .field.is-horizontal
//-         .field-label.is-small
//-             label.label Ability
//-         .field-body
//-             .field
//-             .control
//-                 div.select.is-small.is-fullwidth
//-                 select(x-model="selectedAbilityId", x-bind:disabled="!selectedTechnique")
//-                     option(default) Choose an ability
//-                     template(x-for="ability of filteredAbilities.filter((e) => selectedTechnique === e.technique_id)", :key="ability.ability_id")
//-                     option(x-bind:value="ability.ability_id" x-text="ability.name")
//-         .field.is-horizontal
//-         .field-label.is-small
//-             label.label Description
//-         .field-body
//-             .field
//-             pre(x-text="filteredAbilities.find((e) => selectedAbilityId === e.ability_id)?.description || 'Select an ability to see its description'")
//-     footer.modal-card-foot
//-     nav.level
//-         .level-left
//-         button.button.is-small(@click="showRunModal = false") Close
//-         .level-right
//-         button.button.is-small.is-primary(@click="runAbility()", x-bind:disabled="!selectedAbilityId || running") Run

</template>

<style scoped>
#select-agent {
    max-width: 800px;
    margin: 0 auto;
}

.search-results {
    overflow-y: scroll;
    max-height: 200px;
    background-color: #010101;
    border-radius: 0 4px;
}
.search-results p {
    margin-bottom: 0 !important;
    padding: 5px;
    cursor: pointer;
}
.search-results p:hover {
    background-color: #484848;
}
</style>